"""
블록 클래스 정의
블록의 구조, 해시 계산, PoW 채굴 로직 포함
"""

import hashlib
import json


class Block:
    """블록체인의 개별 블록을 나타내는 클래스"""

    def __init__(self, index, timestamp, transactions, difficulty, previous_hash, miner_id):
        """
        Args:
            index: 블록 높이 (제네시스=0부터 시작)
            timestamp: 블록 생성 시간
            transactions: 블록에 포함된 트랜잭션 리스트
            difficulty: 난이도 (PoW 목표)
            previous_hash: 이전 블록의 해시
            miner_id: 채굴한 노드의 ID
        """
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.difficulty = difficulty
        self.previous_hash = previous_hash
        self.miner_id = miner_id  # 누가 캤는지 (시뮬레이션 용)
        self.nonce = 0
        self.hash = None

        # Work 함수: 2^difficulty (비트연산 1 << difficulty)
        # 난이도가 1 오를 때마다 작업량은 2배가 됨 (Most-work 규칙의 핵심)
        self.block_work = 1 << difficulty
        self.total_work = 0  # 제네시스부터 이 블록까지의 누적 작업량

    def calculate_hash(self):
        """
        블록의 해시를 계산

        Returns:
            str: SHA-256 해시값 (16진수 문자열)
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "difficulty": self.difficulty,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self):
        """
        실제 PoW(작업 증명) 수행
        난이도에 맞는 해시를 찾을 때까지 nonce를 증가시킴
        """
        target = "0" * self.difficulty
        self.nonce = 0

        while True:
            self.hash = self.calculate_hash()
            if self.hash.startswith(target):
                break
            self.nonce += 1

        print(f"[MINE] 블록 채굴 성공 (난이도: {self.difficulty}): {self.hash}")

    def __repr__(self):
        """블록의 문자열 표현"""
        return f"Block(idx={self.index}, hash={self.hash[:8] if self.hash else 'None'}..., work={self.total_work})"
