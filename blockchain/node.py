"""
노드 클래스 정의
블록 검증, 체인 선택, 상태 관리, 채굴 등의 핵심 로직 포함
"""

import hashlib
import json
import copy
from .block import Block
from . import config
from .crypto import CryptoUtils


class Node:
    """블록체인 네트워크의 개별 노드를 나타내는 클래스"""

    def __init__(self, node_id, genesis_block):
        """
        Args:
            node_id: 노드 식별자
            genesis_block: 제네시스 블록
        """
        self.node_id = node_id

        # Block Tree: 모든 블록 저장 (고아 블록 포함)
        # key: block_hash, value: Block 객체
        self.block_index = {genesis_block.hash: genesis_block}

        # 고아 블록 대기실 (Orphan Pool)
        # key: parent_hash (기다리는 부모의 해시)
        # value: [block1, block2...] (그 부모를 기다리는 자식 블록들)
        self.orphan_pool = {}

        # 현재 내가 생각하는 '메인 체인'의 끝 (Tip)
        self.chain_tip = genesis_block.hash

        # Mempool
        self.mempool = []

        # 상태 (UTXO/Balances) - 필요할 때 Replay로 계산
        self.state = {}
        self.rebuild_state(genesis_block.hash)

    def get_tip_block(self):
        """현재 체인의 팁 블록 반환"""
        return self.block_index[self.chain_tip]

    def add_transaction(self, tx):
        """멤풀에 트랜잭션 추가"""
        self.mempool.append(tx)

    # 상태 처리: Replay (Undo Log 대신 다시 계산)
    def rebuild_state(self, tip_hash):
        """
        제네시스부터 tip_hash까지 거슬러 올라가며 경로를 찾고,
        다시 내려오면서 잔액을 계산함.

        Args:
            tip_hash: 목표 팁 블록의 해시

        Returns:
            bool: 성공 여부
        """
        # 1. 경로 찾기 (Tip -> Genesis)
        path = []
        curr = self.block_index.get(tip_hash)
        while curr:
            path.append(curr)
            if curr.previous_hash == "0":  # Genesis 도달
                break
            curr = self.block_index.get(curr.previous_hash)

        # [확인] 경로 불완전 감지
        if not path or path[-1].previous_hash != "0":
            print("[ERROR] 경로 불완전 - 상태 재구성 중단")
            return False

        # 2. 순방향 재생 (Genesis -> Tip)
        new_state = {}
        for block in reversed(path):
            self.apply_block_to_state(block, new_state)

        self.state = new_state
        return True

    def apply_block_to_state(self, block, state):
        """
        블록 내 트랜잭션을 상태에 적용하는 헬퍼 함수

        Args:
            block: 적용할 블록
            state: 상태 딕셔너리
        """
        for tx in block.transactions:
            body = tx['body']
            sender = body['sender']
            recipient = body['recipient']
            amount = body['amount']
            nonce = body.get('nonce', 0)

            # Sender 초기화
            if sender not in state:
                state[sender] = {'balance': 0, 'nonce': 0}
            # Recipient 초기화
            if recipient not in state:
                state[recipient] = {'balance': 0, 'nonce': 0}

            if sender == "SYSTEM":
                # SYSTEM은 nonce 체크 면제 (또는 별도 처리)
                state[recipient]['balance'] += amount
            else:
                # 상태 업데이트: 잔액 차감 + Nonce 증가
                state[sender]['balance'] -= amount
                state[sender]['nonce'] = nonce  # 현재 트랜잭션의 nonce로 업데이트
                state[recipient]['balance'] += amount

    # 체인 선택 (Most-work) & Reorg
    def receive_block(self, new_block):
        """
        새로운 블록을 수신하고 처리

        Args:
            new_block: 수신한 블록
        """
        # 1. 이미 아는 블록이면 무시
        if new_block.hash in self.block_index:
            return

        # 2. 부모 블록 확인 (부모를 모르면 고아 블록 처리)
        parent = self.block_index.get(new_block.previous_hash)

        if not parent:
            # 부모가 아직 도착하지 않음 -> 고아 블록(Orphan)으로 대기실에 보관
            print(f"[ORPHAN] [{self.node_id}] 고아 블록 보관: {new_block.hash[:6]} (부모 {new_block.previous_hash[:6]} 기다림)")

            if new_block.previous_hash not in self.orphan_pool:
                self.orphan_pool[new_block.previous_hash] = []
            self.orphan_pool[new_block.previous_hash].append(new_block)
            return

        # 3. 통합 유효성 검증 호출
        if not self.validate_block(new_block, parent):
            print(f"[REMOVE] [{self.node_id}] 유효하지 않은 블록 폐기: {new_block.hash[:6]}")
            return

        # 4. 누적 작업량(Total Work) 계산
        # 내 작업량 = 부모 작업량 + 내 블록 난이도 가중치
        new_block.total_work = parent.total_work + new_block.block_work

        # 블록 저장소에 추가
        self.block_index[new_block.hash] = new_block

        # Chain Selection (가장 무거운 체인 선택)
        current_tip = self.get_tip_block()

        if new_block.total_work > current_tip.total_work:
            # 1. 단순 연장인지, Reorg인지 판단
            # "새 블록의 부모가 내 현재 팁인가?"
            if new_block.previous_hash == current_tip.hash:
                # [Case A] 정상적인 체인 연장
                print(f"[EXTEND] [{self.node_id}] 체인 연장: {new_block.hash[:6]} (H:{new_block.index})")

                # 새 블록의 트랜잭션만 멤풀에서 빼주면 됨
                for tx in new_block.transactions:
                    if tx in self.mempool:
                        self.mempool.remove(tx)

            else:
                # [Case B] Reorg 발생 (부모가 다름 = 갈라진 가지)
                self.handle_reorg(current_tip, new_block)

            # 2. Tip 업데이트 및 상태 재계산
            # (Reorg 여부와 상관없이 상태는 항상 Tip 기준으로 다시 그림)
            self.chain_tip = new_block.hash
            self.rebuild_state(new_block.hash)

            # Mempool 정리 (새 체인에 포함된 거래는 멤풀에서 제거)
            self.clean_mempool()

        # ---------------------------------------------------------
        # 6. [추가된 부분] 고아 블록 구출 (Recursive Processing)
        # 중요: 이 로직은 위 if문(Chain Selection) 바깥에 있어야 합니다.
        # 부모가 메인 체인으로 선택받지 못했더라도, 자식을 연결하면
        # 자식이 메인 체인을 이길 수도 있기 때문입니다.
        # ---------------------------------------------------------
        children = self.orphan_pool.pop(new_block.hash, [])
        if children:
            print(f"[UNLOCK] [{self.node_id}] 고아 해제! {len(children)}개의 블록을 연결 시도합니다.")
            for child in children:
                self.receive_block(child)

    def validate_block(self, new_block, parent_block):
        """
        [기존 is_chain_valid의 단일 블록 버전]
        새로운 블록이 부모 블록에 대해 유효한지 9가지 항목 정밀 검사

        Args:
            new_block: 검증할 블록
            parent_block: 부모 블록

        Returns:
            bool: 유효성 여부
        """
        # 1. 해시 무결성 검사
        if new_block.hash != new_block.calculate_hash():
            print(f"[ERROR] 오류: 데이터 변조됨 (Hash 불일치)")
            return False

        # 2. 연결 고리 검사
        if new_block.previous_hash != parent_block.hash:
            print(f"[ERROR] 오류: 부모 해시 불일치")
            return False

        # 3. PoW 작업 증명 (해당 난이도 준수 여부)
        target_prefix = "0" * new_block.difficulty
        if not new_block.hash.startswith(target_prefix):
            print(f"[ERROR] 오류: 난이도({new_block.difficulty}) 불충족")
            return False

        # 4. 난이도 조작 여부 검사
        expected = self.get_expected_difficulty(new_block, parent_block)
        if new_block.difficulty != expected:
            print(f"[ERROR] 오류: 난이도 조작됨 (규칙: {expected}, 실제: {new_block.difficulty})")
            return False

        # 5. 블록 단조 증가 검사
        if new_block.timestamp <= parent_block.timestamp:
            print(f"[ERROR] 오류: 시간이 과거로 흐름")
            return False

        # 6. 미래 시간 제한
        if new_block.timestamp > config.SIM_TIME + config.FUTURE_DRIFT:
            print(f"[ERROR] 오류: 미래 시간 블록")
            return False

        # 7. 난이도 급변 제한
        if abs(new_block.difficulty - parent_block.difficulty) > 1:
            print(f"[ERROR] 오류: 난이도 급변")
            return False

        # 8. 비정상적 시간 점프
        if new_block.timestamp - parent_block.timestamp > config.MAX_TIME_JUMP:
            print(f"[WARN] 경고: 시간 점프 과도함")
            # 경고만 하고 통과시킬지, 막을지는 정책 결정 (여기선 일단 True)

        # 9. 트랜잭션 및 상태 검증 (Transaction & State Validation)
        return self.validate_transactions(new_block, parent_block)

    def validate_transactions(self, new_block, parent_block):
        """
        블록 내 트랜잭션의 유효성 검증

        Args:
            new_block: 검증할 블록
            parent_block: 부모 블록

        Returns:
            bool: 유효성 여부
        """
        # 부모 블록까지의 잔액 상태를 가져옴 (Base State)
        temp_state = self.get_state_at(parent_block.hash)

        coinbase_count = 0

        for tx in new_block.transactions:
            body = tx['body']  # Body 추출
            sender = body['sender']
            recipient = body['recipient']
            amount = body['amount']
            tx_nonce = body.get('nonce', 0)

            # Sender/Recipient 상태 가져오기 (없으면 기본값)
            sender_acc = temp_state.get(sender, {'balance': 0, 'nonce': 0})
            recipient_acc = temp_state.get(recipient, {'balance': 0, 'nonce': 0})

            # A. 기본 무결성 체크
            if amount <= 0:
                print(f"[ERROR] 오류: 0 이하의 금액 거래 발견")
                return False
            if sender == recipient:
                print(f"[ERROR] 오류: 자기 자신에게 송금")
                return False

            # B. SYSTEM (Coinbase) 거래 검증
            if sender == "SYSTEM":
                coinbase_count += 1

                if coinbase_count > 1:
                    print(f"[ERROR] 오류: 하나의 블록에 보상 거래가 2개 이상임")
                    return False

                if amount != config.MINING_REWARD:
                    print(f"[ERROR] 오류: 채굴 보상 금액 불일치 ({amount} != {config.MINING_REWARD})")
                    return False

                if recipient != new_block.miner_id:
                    print(f"[ERROR] 오류: 채굴 보상을 엉뚱한 사람이 가져감 ({recipient} != {new_block.miner_id})")
                    return False

                # 상태 반영 (돈이 생겨남)
                recipient_acc['balance'] += amount
                temp_state[recipient] = recipient_acc  # 업데이트 된 객체 저장

            # C. 일반 거래 검증
            else:
                # [NEW] 서명 검증 (디지털 서명)
                if not self.verify_transaction_signature(tx):
                    print(f"[ERROR] 오류: 서명 검증 실패 (Sender: {sender})")
                    return False

                # 잔액 부족 체크
                if sender_acc['balance'] < amount:
                    print(f"[ERROR] 오류: 잔액 부족 (Sender: {sender}, Need: {amount}, Has: {sender_acc['balance']})")
                    return False

                # Nonce 검증 (Replay Protection)
                expected_nonce = sender_acc['nonce'] + 1
                if tx_nonce != expected_nonce:
                    print(f"[ERROR] 오류: Nonce 불일치 ({sender}). Exp: {expected_nonce}, Got: {tx_nonce}")
                    return False

                # 상태 반영
                sender_acc['balance'] -= amount
                sender_acc['nonce'] = tx_nonce  # Nonce 증가
                recipient_acc['balance'] += amount

                # 변경된 상태 저장
                temp_state[sender] = sender_acc
                temp_state[recipient] = recipient_acc

        # D. 코인베이스 존재 여부 확인
        if coinbase_count == 0:
            print(f"[ERROR] 오류: 채굴 보상(Coinbase) 트랜잭션이 누락됨")
            return False

        return True

    def verify_transaction_signature(self, tx):
        """
        트랜잭션의 디지털 서명 검증

        Args:
            tx: 검증할 트랜잭션

        Returns:
            bool: 서명이 유효한지 여부
        """
        try:
            # 1. 트랜잭션에 필수 필드가 있는지 확인
            if 'signature' not in tx or 'public_key' not in tx:
                print(f"[ERROR] 서명 검증 실패: 서명 또는 공개키 누락")
                return False

            # 2. 공개키 복원
            public_key_hex = tx['public_key']
            public_key_bytes = bytes.fromhex(public_key_hex)
            public_key = CryptoUtils.bytes_to_public_key(public_key_bytes)

            # 3. 공개키로부터 주소 계산
            calculated_address = CryptoUtils.public_key_to_address(public_key)

            # 4. 송신자 주소와 공개키가 일치하는지 확인
            sender_address = tx['body']['sender']
            if calculated_address != sender_address:
                print(f"[ERROR] 서명 검증 실패: 공개키가 송신자 주소와 불일치")
                return False

            # 5. 서명 복원
            signature_hex = tx['signature']
            signature = CryptoUtils.hex_to_signature(signature_hex)

            # 6. 서명 검증 (body만 사용)
            is_valid = CryptoUtils.verify_signature(public_key, tx['body'], signature)

            return is_valid

        except Exception as e:
            print(f"[ERROR] 서명 검증 중 예외 발생: {e}")
            return False

    def get_ancestor(self, block, target_height):
        """
        블록에서 부모를 타고 거슬러 올라가 target_height의 블록을 찾음

        Args:
            block: 시작 블록
            target_height: 목표 높이

        Returns:
            Block: 찾은 블록 또는 None
        """
        curr = block
        while curr and curr.index > target_height:
            curr = self.block_index.get(curr.previous_hash)
        return curr

    def get_expected_difficulty(self, new_block, parent_block):
        """
        [트리 구조 전용] 다음에 올 블록의 적정 난이도 계산

        Args:
            new_block: 새 블록
            parent_block: 부모 블록

        Returns:
            int: 예상 난이도
        """
        # 1. 첫 구간(Genesis 근처)은 기본 난이도
        if new_block.index <= config.ADJUSTMENT_INTERVAL:
            return config.DEFAULT_DIFFICULTY

        # 2. 조정 주기가 아니라면 부모 난이도 유지
        if new_block.index % config.ADJUSTMENT_INTERVAL != 0:
            return parent_block.difficulty

        # 3. 조정 주기 도달: 과거 블록 시간 측정
        start_index = new_block.index - config.ADJUSTMENT_INTERVAL

        # 부모 블록에서부터 뒤로 거슬러 올라가서 찾음
        start_node = self.get_ancestor(parent_block, start_index)

        if not start_node:
            return parent_block.difficulty  # 안전장치

        time_taken = parent_block.timestamp - start_node.timestamp
        expected_time = config.TARGET_BLOCK_TIME * config.ADJUSTMENT_INTERVAL

        if time_taken < expected_time / 2:
            return parent_block.difficulty + config.MAX_STEP
        elif time_taken > expected_time * 2:
            return max(parent_block.difficulty - config.MAX_STEP, 1)
        else:
            return parent_block.difficulty

    def get_state_at(self, tip_hash):
        """
        [Helper] 특정 블록(tip_hash) 시점의 잔액 상태를 처음부터 계산해서 반환

        Args:
            tip_hash: 목표 블록 해시

        Returns:
            dict: 상태 딕셔너리
        """
        # 1. 경로 역추적 (Tip -> Genesis)
        path = []
        curr = self.block_index.get(tip_hash)

        while curr:
            path.append(curr)
            if curr.previous_hash == "0":  # Genesis 도달
                break
            curr = self.block_index.get(curr.previous_hash)

        # 2. 경로가 끊겨있거나 Genesis에 도달 못한 경우 (안전장치)
        if not path or path[-1].previous_hash != "0":
            return {}

        # 3. 순방향 재생 (Genesis -> Tip)
        balances = {}
        for block in reversed(path):
            self.apply_block_to_state(block, balances)

        return balances

    def handle_reorg(self, old_tip, new_tip):
        """
        Deep Reorg 처리

        Args:
            old_tip: 이전 팁 블록
            new_tip: 새 팁 블록
        """
        fork_point = None
        discarded_blocks = []  # 버려질 블록들 (Old Chain)
        adopted_blocks = []    # 채택될 블록들 (New Chain)

        curr_old = old_tip
        curr_new = new_tip

        # 1. 높이 맞추기
        while curr_new.index > curr_old.index:
            adopted_blocks.append(curr_new)
            curr_new = self.block_index.get(curr_new.previous_hash)
            if curr_new is None:
                print(f"[WARN] [{self.node_id}] reorg 보류: new 쪽 조상 미수신")
                return

        while curr_old.index > curr_new.index:
            discarded_blocks.append(curr_old)
            curr_old = self.block_index.get(curr_old.previous_hash)
            if curr_old is None:
                print(f"[WARN] [{self.node_id}] reorg 보류: old 쪽 조상 미수신")
                return

        # 2. 공통 조상 찾기
        while curr_new.hash != curr_old.hash:
            adopted_blocks.append(curr_new)
            discarded_blocks.append(curr_old)

            curr_new = self.block_index.get(curr_new.previous_hash)
            curr_old = self.block_index.get(curr_old.previous_hash)

            if curr_new is None or curr_old is None:
                print(f"[WARN] [{self.node_id}] reorg 보류: 공통 조상 탐색 중 조상 미수신")
                return

        fork_point = curr_new  # 공통 조상 발견

        # 3. 멤풀 업데이트
        print(f"[REORG] [{self.node_id}] Reorg 감지! 깊이: {len(discarded_blocks)} block(s) rollback.")

        # 버려지는 블록의 거래들을 멤풀로 부활
        for block in discarded_blocks:
            for tx in block.transactions:
                if tx['body']['sender'] == "SYSTEM":
                    continue  # 코인베이스 제외
                if tx not in self.mempool:
                    self.mempool.append(tx)

        # 새로 채택된 블록의 거래들은 멤풀에서 제거
        for block in adopted_blocks:
            for tx in block.transactions:
                if tx in self.mempool:
                    self.mempool.remove(tx)

    def compute_txid(self, tx):
        """
        서명(sig)을 제외한 body만 해싱하여 ID 생성

        Args:
            tx: 트랜잭션

        Returns:
            str: 트랜잭션 ID (해시)
        """
        return hashlib.sha256(json.dumps(tx['body'], sort_keys=True).encode()).hexdigest()

    def clean_mempool(self):
        """
        멤풀 정리 (Mempool Cleanup)
        현재 메인 체인에 포함된 거래 및 유효하지 않은 거래 제거
        """
        # (1) 현재 메인 체인의 모든 트랜잭션 수집
        confirmed_txs = set()
        curr_block = self.get_tip_block()

        while True:
            for tx in curr_block.transactions:
                tx_sig = self.compute_txid(tx)
                confirmed_txs.add(tx_sig)

            if curr_block.previous_hash == "0":
                break
            curr_block = self.block_index[curr_block.previous_hash]

        # (2) 멤풀 필터링
        valid_mempool = []
        temp_state = copy.deepcopy(self.state)

        for tx in self.mempool:
            tx_sig = self.compute_txid(tx)
            body = tx['body']
            sender = body['sender']
            amount = body['amount']
            tx_nonce = body.get('nonce', 0)

            # 필터 1: 이미 체인에 존재하는가?
            if tx_sig in confirmed_txs:
                continue

            # 필터 2: SYSTEM 거래인가?
            if sender == "SYSTEM":
                continue

            sender_acc = temp_state.get(sender, {'balance': 0, 'nonce': 0})

            # 필터 3: 서명 검증
            if not self.verify_transaction_signature(tx):
                print(f"[REMOVE] [{self.node_id}] 서명 무효 거래 제거: {sender}")
                continue

            # 필터 4: 잔액이 충분한가?
            if sender_acc['balance'] < amount:
                print(f"[REMOVE] [{self.node_id}] 잔액 부족 거래 제거: {sender} (보유: {sender_acc['balance']}, 시도: {amount})")
                continue

            # 필터 5: Nonce 체크
            if tx_nonce == sender_acc['nonce'] + 1:
                sender_acc['balance'] -= amount
                sender_acc['nonce'] = tx_nonce
                temp_state[sender] = sender_acc
                valid_mempool.append(tx)
            else:
                print(f"[REMOVE] [{self.node_id}] nonce 불일치 거래 제거: {sender} (node 상태: {sender_acc['nonce']})")

        # 필터링된 유효 거래들로 멤풀 교체
        self.mempool = valid_mempool

    def try_mine(self):
        """
        채굴 시도: 멤풀에서 트랜잭션을 선택하고 새 블록 생성

        Returns:
            Block: 채굴된 블록
        """
        tip = self.get_tip_block()

        # 보상 트랜잭션
        coinbase_body = {
            "sender": "SYSTEM",
            "recipient": self.node_id,
            "amount": config.MINING_REWARD,
            "nonce": 0
        }
        coinbase_tx = {"body": coinbase_body, "sig": None}

        # 멤풀에서 트랜잭션 선택
        selected_txs = copy.deepcopy(self.select_txs_for_block(max_txs=config.MAX_TXS_PER_BLOCK))

        # 최종 트랜잭션 리스트
        txs = [coinbase_tx] + selected_txs

        # 새 블록 생성
        new_block = Block(
            index=tip.index + 1,
            timestamp=config.SIM_TIME,
            transactions=txs,
            difficulty=tip.difficulty,
            previous_hash=tip.hash,
            miner_id=self.node_id
        )

        # 프로토콜 규칙에 따른 난이도 계산
        expected_difficulty = self.get_expected_difficulty(new_block, tip)

        if new_block.difficulty != expected_difficulty:
            print(f"[CONFIG] [{self.node_id}] 난이도 조정 적용: {new_block.difficulty} -> {expected_difficulty}")
            new_block.difficulty = expected_difficulty
            new_block.block_work = 1 << expected_difficulty

        # 채굴 시도
        new_block.mine_block()
        return new_block

    def select_txs_for_block(self, max_txs=5):
        """
        멤풀에서 유효한 거래만 선별

        Args:
            max_txs: 최대 선택 거래 수

        Returns:
            list: 선택된 트랜잭션 리스트
        """
        selected = []
        temp_state = copy.deepcopy(self.state)

        for tx in self.mempool:
            body = tx['body']
            sender = body['sender']
            amount = body['amount']
            tx_nonce = body.get('nonce', 0)
            sender_acc = temp_state.get(sender, {'balance': 0, 'nonce': 0})

            # 시스템 거래 필터링
            if sender == "SYSTEM":
                continue

            # 서명 검증
            if not self.verify_transaction_signature(tx):
                continue

            # 잔액 및 Nonce 확인
            if sender_acc['balance'] >= amount and tx_nonce == sender_acc['nonce'] + 1:
                sender_acc['balance'] -= amount
                sender_acc['nonce'] = tx_nonce
                temp_state[sender] = sender_acc
                selected.append(tx)

            # 최대 개수 도달 시 중단
            if len(selected) >= max_txs:
                break

        return selected
