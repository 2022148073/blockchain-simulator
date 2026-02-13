"""
네트워크 시뮬레이터 클래스
여러 노드를 관리하고 블록 전파를 시뮬레이션
"""

import random
import copy
from .block import Block
from .node import Node
from . import config


class NetworkSimulator:
    """블록체인 네트워크 시뮬레이터"""

    def __init__(self):
        """네트워크 시뮬레이터 초기화"""
        self.nodes = []
        self.wallets = {}  # {address: Wallet} - 주소별 지갑 매핑
        self.genesis_block = self.create_genesis()

    def create_genesis(self):
        """
        제네시스 블록 생성

        Returns:
            Block: 제네시스 블록
        """
        genesis = Block(
            index=0,
            timestamp=0,
            transactions=[],
            difficulty=config.DEFAULT_DIFFICULTY,
            previous_hash="0",
            miner_id="GENESIS"
        )
        genesis.total_work = genesis.block_work
        genesis.mine_block()
        return genesis

    def add_node(self, node):
        """
        네트워크에 노드 추가

        Args:
            node: 추가할 노드
        """
        self.nodes.append(node)

    def register_wallet(self, wallet):
        """
        지갑을 네트워크에 등록

        Args:
            wallet: 등록할 지갑
        """
        self.wallets[wallet.address] = wallet
        print(f"[WALLET] 지갑 등록: {wallet.owner_name} ({wallet.address[:16]}...)")

    def broadcast_block(self, sender_node, new_block):
        """
        블록을 네트워크에 전파 (네트워크 지연 시뮬레이션 가능)

        Args:
            sender_node: 블록을 전송하는 노드
            new_block: 전파할 블록
        """
        for node in self.nodes:
            if node.node_id != sender_node.node_id:
                # 즉시 전달 (지연 시간 0 가정)
                # deepcopy로 각 노드가 독립적인 블록 객체를 받도록 함
                node.receive_block(copy.deepcopy(new_block))

    def run_simulation(self, steps=20):
        """
        시뮬레이션 실행

        Args:
            steps: 시뮬레이션 스텝 수
        """
        print(f"[START] 시뮬레이션 시작 (Genesis Hash: {self.genesis_block.hash[:6]})")

        for step in range(steps):
            config.SIM_TIME += 1  # 전역 시간 증가
            print(f"\n--- Time: {config.SIM_TIME} ---")

            # 모든 노드가 채굴 시도
            for node in self.nodes:
                # 확률적으로 채굴 시도 (노드 간 경쟁 시뮬레이션)
                if random.random() < config.MINING_PROBABILITY:
                    mined_block = node.try_mine()

                    # 자기 자신에게 등록
                    node.receive_block(mined_block)

                    # 채굴 성공 로그
                    print(f"[MINE]  [{node.node_id}] 블록 채굴 성공! (Work: {mined_block.total_work})")

                    # 네트워크 전파
                    self.broadcast_block(node, mined_block)

            # 상태 출력
            self.print_network_status()

    def print_network_status(self):
        """현재 네트워크 상태 출력"""
        for node in self.nodes:
            tip = node.get_tip_block()
            balance = node.state.get(node.node_id, {'balance': 0, 'nonce': 0})
            print(f"   Node[{node.node_id}]: Tip={tip.hash[:6]}(H:{tip.index}, Work:{tip.total_work}) | Bal={balance}")

    def add_transaction_to_network(self, sender_address, recipient_address, amount):
        """
        네트워크의 모든 노드에 트랜잭션 추가 (브로드캐스트)
        지갑을 사용하여 서명된 트랜잭션 생성

        Args:
            sender_address: 송신자 주소
            recipient_address: 수신자 주소
            amount: 금액
        """
        # 송신자 지갑 확인
        sender_wallet = self.wallets.get(sender_address)
        if not sender_wallet:
            print(f"[ERROR] 오류: 송신자 지갑을 찾을 수 없습니다 ({sender_address[:16]}...)")
            return

        # 송신자의 현재 nonce 확인 (첫 번째 노드 기준)
        if self.nodes:
            sender_state = self.nodes[0].state.get(sender_address, {'balance': 0, 'nonce': 0})
            next_nonce = sender_state['nonce'] + 1
        else:
            next_nonce = 1

        # 지갑을 사용하여 서명된 트랜잭션 생성
        tx = sender_wallet.create_transaction(recipient_address, amount, next_nonce)

        # 모든 노드에 추가
        for node in self.nodes:
            node.add_transaction(copy.deepcopy(tx))

        sender_name = sender_wallet.owner_name
        recipient_wallet = self.wallets.get(recipient_address)
        recipient_name = recipient_wallet.owner_name if recipient_wallet else recipient_address[:8]

        print(f"[BROADCAST] 트랜잭션 브로드캐스트: {sender_name} -> {recipient_name}: {amount} (nonce: {next_nonce})")
