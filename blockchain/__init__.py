"""
블록체인 합의 시뮬레이터 패키지

이 패키지는 비트코인과 유사한 PoW 합의 알고리즘을 시뮬레이션합니다.

주요 모듈:
    - block: Block 클래스 정의
    - node: Node 클래스 정의 (합의 로직 포함)
    - network: NetworkSimulator 클래스 정의
    - config: 시스템 설정 및 상수
    - crypto: 암호화 유틸리티 (ECDSA 키 생성, 서명, 검증)
    - wallet: Wallet 클래스 (개인키 관리, 트랜잭션 서명)
"""

from .block import Block
from .node import Node
from .network import NetworkSimulator
from .wallet import Wallet, WalletManager
from .crypto import CryptoUtils
from . import config

__all__ = ['Block', 'Node', 'NetworkSimulator', 'Wallet', 'WalletManager', 'CryptoUtils', 'config']
__version__ = '2.0.0'
