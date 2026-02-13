"""
암호화 모듈
ECDSA 기반 키 생성, 서명, 검증 기능 제공
"""

import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


class CryptoUtils:
    """암호화 유틸리티 클래스"""

    @staticmethod
    def generate_key_pair():
        """
        ECDSA 키 쌍 생성 (secp256k1 - 비트코인과 동일한 곡선)

        Returns:
            tuple: (private_key, public_key) 객체
        """
        # secp256k1 곡선 사용 (비트코인과 동일)
        private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def private_key_to_bytes(private_key):
        """
        개인키를 바이트로 직렬화

        Args:
            private_key: 개인키 객체

        Returns:
            bytes: 직렬화된 개인키
        """
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    @staticmethod
    def public_key_to_bytes(public_key):
        """
        공개키를 바이트로 직렬화

        Args:
            public_key: 공개키 객체

        Returns:
            bytes: 직렬화된 공개키
        """
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def bytes_to_private_key(key_bytes):
        """
        바이트에서 개인키 객체 복원

        Args:
            key_bytes: 직렬화된 개인키

        Returns:
            개인키 객체
        """
        return serialization.load_pem_private_key(
            key_bytes,
            password=None,
            backend=default_backend()
        )

    @staticmethod
    def bytes_to_public_key(key_bytes):
        """
        바이트에서 공개키 객체 복원

        Args:
            key_bytes: 직렬화된 공개키

        Returns:
            공개키 객체
        """
        return serialization.load_pem_public_key(
            key_bytes,
            backend=default_backend()
        )

    @staticmethod
    def public_key_to_address(public_key):
        """
        공개키에서 주소 생성 (SHA-256 해시 사용)

        Args:
            public_key: 공개키 객체

        Returns:
            str: 주소 (16진수 문자열)
        """
        pub_bytes = CryptoUtils.public_key_to_bytes(public_key)
        # SHA-256 해싱
        hash_result = hashlib.sha256(pub_bytes).digest()
        # 다시 SHA-256 (비트코인은 RIPEMD160도 사용하지만 여기선 단순화)
        address_hash = hashlib.sha256(hash_result).hexdigest()
        # 앞 40자만 사용 (주소 길이 단축)
        return address_hash[:40]

    @staticmethod
    def sign_message(private_key, message):
        """
        메시지에 서명

        Args:
            private_key: 개인키 객체
            message: 서명할 메시지 (문자열 또는 딕셔너리)

        Returns:
            bytes: 서명
        """
        # 메시지를 바이트로 변환
        if isinstance(message, dict):
            message_bytes = json.dumps(message, sort_keys=True).encode('utf-8')
        elif isinstance(message, str):
            message_bytes = message.encode('utf-8')
        else:
            message_bytes = message

        # ECDSA 서명 생성
        signature = private_key.sign(
            message_bytes,
            ec.ECDSA(hashes.SHA256())
        )
        return signature

    @staticmethod
    def verify_signature(public_key, message, signature):
        """
        서명 검증

        Args:
            public_key: 공개키 객체
            message: 원본 메시지 (문자열 또는 딕셔너리)
            signature: 서명 (bytes)

        Returns:
            bool: 검증 성공 여부
        """
        try:
            # 메시지를 바이트로 변환
            if isinstance(message, dict):
                message_bytes = json.dumps(message, sort_keys=True).encode('utf-8')
            elif isinstance(message, str):
                message_bytes = message.encode('utf-8')
            else:
                message_bytes = message

            # 서명 검증
            public_key.verify(
                signature,
                message_bytes,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"서명 검증 오류: {e}")
            return False

    @staticmethod
    def signature_to_hex(signature):
        """
        서명을 16진수 문자열로 변환

        Args:
            signature: 서명 (bytes)

        Returns:
            str: 16진수 문자열
        """
        return signature.hex()

    @staticmethod
    def hex_to_signature(hex_string):
        """
        16진수 문자열을 서명으로 변환

        Args:
            hex_string: 16진수 문자열

        Returns:
            bytes: 서명
        """
        return bytes.fromhex(hex_string)


def demo():
    """암호화 기능 데모"""
    print("=" * 60)
    print("암호화 기능 데모")
    print("=" * 60)

    # 1. 키 쌍 생성
    print("\n1. 키 쌍 생성")
    private_key, public_key = CryptoUtils.generate_key_pair()
    address = CryptoUtils.public_key_to_address(public_key)
    print(f"   주소: {address}")

    # 2. 메시지 서명
    print("\n2. 메시지 서명")
    message = {"sender": "Alice", "recipient": "Bob", "amount": 10}
    signature = CryptoUtils.sign_message(private_key, message)
    print(f"   메시지: {message}")
    print(f"   서명 (앞 32바이트): {signature[:32].hex()}")

    # 3. 서명 검증 (올바른 공개키)
    print("\n3. 서명 검증 (올바른 공개키)")
    is_valid = CryptoUtils.verify_signature(public_key, message, signature)
    print(f"   검증 결과: {'[OK] 성공' if is_valid else '[FAIL] 실패'}")

    # 4. 서명 검증 (잘못된 메시지)
    print("\n4. 서명 검증 (변조된 메시지)")
    tampered_message = {"sender": "Alice", "recipient": "Bob", "amount": 1000}
    is_valid = CryptoUtils.verify_signature(public_key, tampered_message, signature)
    print(f"   변조된 메시지: {tampered_message}")
    print(f"   검증 결과: {'[OK] 성공' if is_valid else '[FAIL] 실패 (예상된 결과)'}")

    # 5. 서명 검증 (잘못된 공개키)
    print("\n5. 서명 검증 (다른 사람의 공개키)")
    other_private_key, other_public_key = CryptoUtils.generate_key_pair()
    is_valid = CryptoUtils.verify_signature(other_public_key, message, signature)
    print(f"   검증 결과: {'[OK] 성공' if is_valid else '[FAIL] 실패 (예상된 결과)'}")


if __name__ == "__main__":
    demo()
