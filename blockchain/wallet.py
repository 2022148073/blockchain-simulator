"""
지갑 모듈
개인키/공개키 관리 및 트랜잭션 서명 기능 제공
"""

import json
from .crypto import CryptoUtils


class Wallet:
    """
    사용자 지갑 클래스
    개인키를 안전하게 보관하고 트랜잭션에 서명하는 기능 제공
    """

    def __init__(self, owner_name=None):
        """
        새 지갑 생성

        Args:
            owner_name: 지갑 소유자 이름 (선택적)
        """
        # 새로운 키 쌍 생성
        self.private_key, self.public_key = CryptoUtils.generate_key_pair()

        # 공개키에서 주소 생성
        self.address = CryptoUtils.public_key_to_address(self.public_key)

        # 소유자 이름 (디버깅/표시용)
        self.owner_name = owner_name if owner_name else self.address[:8]

    @classmethod
    def from_private_key(cls, private_key_bytes, owner_name=None):
        """
        기존 개인키로부터 지갑 복원

        Args:
            private_key_bytes: 직렬화된 개인키
            owner_name: 지갑 소유자 이름 (선택적)

        Returns:
            Wallet: 복원된 지갑 객체
        """
        wallet = cls.__new__(cls)
        wallet.private_key = CryptoUtils.bytes_to_private_key(private_key_bytes)
        wallet.public_key = wallet.private_key.public_key()
        wallet.address = CryptoUtils.public_key_to_address(wallet.public_key)
        wallet.owner_name = owner_name if owner_name else wallet.address[:8]
        return wallet

    def get_address(self):
        """
        지갑 주소 반환

        Returns:
            str: 지갑 주소
        """
        return self.address

    def get_public_key_bytes(self):
        """
        공개키를 바이트로 반환

        Returns:
            bytes: 직렬화된 공개키
        """
        return CryptoUtils.public_key_to_bytes(self.public_key)

    def get_public_key_hex(self):
        """
        공개키를 16진수 문자열로 반환

        Returns:
            str: 16진수 공개키
        """
        return self.get_public_key_bytes().hex()

    def sign_transaction(self, tx_body):
        """
        트랜잭션에 서명

        Args:
            tx_body: 트랜잭션 본문 (딕셔너리)

        Returns:
            str: 서명 (16진수 문자열)
        """
        signature = CryptoUtils.sign_message(self.private_key, tx_body)
        return CryptoUtils.signature_to_hex(signature)

    def create_transaction(self, recipient, amount, nonce):
        """
        새 트랜잭션 생성 및 서명

        Args:
            recipient: 수신자 주소
            amount: 전송 금액
            nonce: 트랜잭션 nonce

        Returns:
            dict: 서명된 트랜잭션
        """
        # 트랜잭션 본문 생성
        tx_body = {
            "sender": self.address,
            "recipient": recipient,
            "amount": amount,
            "nonce": nonce
        }

        # 서명 생성
        signature = self.sign_transaction(tx_body)

        # 공개키도 포함 (검증을 위해)
        transaction = {
            "body": tx_body,
            "signature": signature,
            "public_key": self.get_public_key_hex()
        }

        return transaction

    def export_private_key(self):
        """
        개인키를 내보내기 (백업용)
        [WARN] 주의: 개인키는 절대 공개하면 안 됩니다!

        Returns:
            bytes: 직렬화된 개인키
        """
        return CryptoUtils.private_key_to_bytes(self.private_key)

    def __repr__(self):
        """지갑의 문자열 표현"""
        return f"Wallet(owner={self.owner_name}, address={self.address[:16]}...)"

    def __str__(self):
        """지갑 정보 출력"""
        return f"지갑 소유자: {self.owner_name}\n주소: {self.address}"


class WalletManager:
    """여러 지갑을 관리하는 매니저 클래스"""

    def __init__(self):
        """지갑 매니저 초기화"""
        self.wallets = {}  # {name: Wallet}

    def create_wallet(self, name):
        """
        새 지갑 생성

        Args:
            name: 지갑 이름

        Returns:
            Wallet: 생성된 지갑
        """
        if name in self.wallets:
            print(f"[WARN] 경고: '{name}' 지갑이 이미 존재합니다.")
            return self.wallets[name]

        wallet = Wallet(owner_name=name)
        self.wallets[name] = wallet
        print(f"[OK] '{name}' 지갑 생성 완료")
        print(f"   주소: {wallet.address}")
        return wallet

    def get_wallet(self, name):
        """
        지갑 가져오기

        Args:
            name: 지갑 이름

        Returns:
            Wallet: 지갑 객체 또는 None
        """
        return self.wallets.get(name)

    def get_address(self, name):
        """
        지갑 주소 가져오기

        Args:
            name: 지갑 이름

        Returns:
            str: 주소 또는 None
        """
        wallet = self.get_wallet(name)
        return wallet.address if wallet else None

    def list_wallets(self):
        """모든 지갑 목록 출력"""
        print("\n[WALLETS] 지갑 목록:")
        for name, wallet in self.wallets.items():
            print(f"   [{name}] {wallet.address}")


def demo():
    """지갑 기능 데모"""
    print("=" * 60)
    print("지갑 기능 데모")
    print("=" * 60)

    # 1. 지갑 생성
    print("\n1. 지갑 생성")
    alice_wallet = Wallet("Alice")
    print(f"   {alice_wallet}")

    bob_wallet = Wallet("Bob")
    print(f"   {bob_wallet}")

    # 2. 트랜잭션 생성 및 서명
    print("\n2. 트랜잭션 생성 및 서명")
    tx = alice_wallet.create_transaction(
        recipient=bob_wallet.address,
        amount=10,
        nonce=1
    )
    print(f"   송신자: {tx['body']['sender'][:16]}...")
    print(f"   수신자: {tx['body']['recipient'][:16]}...")
    print(f"   금액: {tx['body']['amount']}")
    print(f"   서명 (앞 32자): {tx['signature'][:32]}...")

    # 3. 서명 검증
    print("\n3. 서명 검증")
    public_key_bytes = bytes.fromhex(tx['public_key'])
    public_key = CryptoUtils.bytes_to_public_key(public_key_bytes)
    signature = CryptoUtils.hex_to_signature(tx['signature'])

    is_valid = CryptoUtils.verify_signature(public_key, tx['body'], signature)
    print(f"   검증 결과: {'[OK] 성공' if is_valid else '[FAIL] 실패'}")

    # 4. 지갑 매니저 사용
    print("\n4. 지갑 매니저 사용")
    manager = WalletManager()
    manager.create_wallet("Alice")
    manager.create_wallet("Bob")
    manager.create_wallet("Charlie")
    manager.list_wallets()


if __name__ == "__main__":
    demo()
