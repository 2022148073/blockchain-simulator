# 블록체인 합의 시뮬레이터 v2.0 (암호화 버전)

비트코인과 유사한 PoW(Proof of Work) 합의 알고리즘과 **ECDSA 디지털 서명**을 시뮬레이션하는 모듈화된 Python 프로젝트입니다.

## 🆕 v2.0 새로운 기능

- ✅ **ECDSA 디지털 서명**: secp256k1 곡선 사용 (비트코인과 동일)
- ✅ **지갑 시스템**: 개인키/공개키 쌍 자동 생성
- ✅ **주소 기반 식별**: 공개키 해시로 주소 생성
- ✅ **트랜잭션 서명 검증**: 블록 검증 시 서명 자동 확인
- ✅ **위조 방지**: 서명 없는 트랜잭션은 블록에 포함 불가

## 📁 프로젝트 구조

```
blockchain/
├── __init__.py          # 패키지 초기화 파일
├── config.py            # 시스템 설정 및 상수
├── block.py             # Block 클래스
├── node.py              # Node 클래스 (합의 로직 + 서명 검증)
├── network.py           # NetworkSimulator 클래스
├── crypto.py            # 암호화 유틸리티 (ECDSA)
├── wallet.py            # Wallet 클래스 (키 관리)
├── main.py              # 실행 스크립트
└── README.md            # 이 파일
```

## 🔧 모듈 설명

### 1. **config.py**
- 전역 변수 및 시스템 상수 정의
- 주요 설정:
  - `ADJUSTMENT_INTERVAL`: 난이도 조절 주기 (3블록)
  - `TARGET_BLOCK_TIME`: 목표 블록 생성 시간 (2초)
  - `MINING_REWARD`: 채굴 보상 (50)
  - `DEFAULT_DIFFICULTY`: 초기 난이도 (2)

### 2. **block.py**
- `Block` 클래스 정의
- 주요 기능:
  - 블록 해시 계산 (`calculate_hash()`)
  - PoW 채굴 (`mine_block()`)
  - 작업량(Work) 계산 (2^difficulty)

### 3. **node.py**
- `Node` 클래스 정의
- 핵심 기능:
  - 블록 수신 및 검증 (`receive_block()`, `validate_block()`)
  - **🆕 디지털 서명 검증** (`verify_transaction_signature()`)
  - 체인 선택 (Most-work 규칙)
  - 체인 재구성 (Reorg) 처리 (`handle_reorg()`)
  - 상태 관리 (Replay 방식)
  - 고아 블록 처리
  - 멤풀 관리 (서명 무효 거래 자동 제거)
  - 채굴 (`try_mine()`)

### 4. **network.py**
- `NetworkSimulator` 클래스 정의
- 주요 기능:
  - 제네시스 블록 생성
  - 노드 관리
  - **🆕 지갑 등록** (`register_wallet()`)
  - **🆕 서명된 트랜잭션 브로드캐스트**

### 5. **crypto.py** 🆕
- `CryptoUtils` 클래스: 암호화 유틸리티
- 주요 기능:
  - **ECDSA 키 쌍 생성** (secp256k1 곡선)
  - **디지털 서명 생성** (`sign_message()`)
  - **서명 검증** (`verify_signature()`)
  - **주소 생성** (공개키 → SHA-256 해시)
  - 키 직렬화/역직렬화

### 6. **wallet.py** 🆕
- `Wallet` 클래스: 사용자 지갑
- 주요 기능:
  - **자동 키 쌍 생성**
  - **주소 관리**
  - **트랜잭션 서명** (`create_transaction()`)
  - **개인키 백업/복원**
- `WalletManager` 클래스: 여러 지갑 관리

### 7. **main.py**
- 실행 진입점
- 3가지 데모 포함:
  - `main()`: 기본 시뮬레이션 (서명 검증 포함)
  - `demo_with_transactions()`: 트랜잭션 데모
  - `demo_signature_validation()`: 서명 검증 상세 데모

## 🚀 실행 방법

### 기본 실행
```bash
# 방법 1: 모듈로 실행
python -m blockchain.main

# 방법 2: 직접 실행
python blockchain/main.py
```

### 코드에서 사용 (v2.0 - 암호화 버전)
```python
from blockchain import Node, NetworkSimulator, Wallet, config

# 네트워크 생성
network = NetworkSimulator()

# 지갑 생성 (자동으로 개인키/공개키 생성)
wallet_alice = Wallet("Alice")
wallet_bob = Wallet("Bob")

# 지갑을 네트워크에 등록
network.register_wallet(wallet_alice)
network.register_wallet(wallet_bob)

# 노드 생성 (지갑 주소를 ID로 사용)
alice = Node(wallet_alice.address, network.genesis_block)
bob = Node(wallet_bob.address, network.genesis_block)
network.add_node(alice)
network.add_node(bob)

# 시뮬레이션 실행
network.run_simulation(steps=5)

# 서명된 트랜잭션 생성 및 전송
network.add_transaction_to_network(
    wallet_alice.address,  # 송신자
    wallet_bob.address,    # 수신자
    amount=10
)

# 추가 채굴
network.run_simulation(steps=10)
```

### 암호화 기능 사용
```python
from blockchain import Wallet, CryptoUtils

# 1. 지갑 생성
alice_wallet = Wallet("Alice")
print(f"주소: {alice_wallet.address}")

# 2. 트랜잭션 생성 및 서명
tx = alice_wallet.create_transaction(
    recipient="bob_address_here",
    amount=10,
    nonce=1
)

# 트랜잭션 구조:
# {
#     "body": {"sender": "...", "recipient": "...", "amount": 10, "nonce": 1},
#     "signature": "...",  # ECDSA 서명 (hex)
#     "public_key": "..."  # 공개키 (hex)
# }

# 3. 서명 검증
public_key = CryptoUtils.bytes_to_public_key(bytes.fromhex(tx['public_key']))
signature = CryptoUtils.hex_to_signature(tx['signature'])
is_valid = CryptoUtils.verify_signature(public_key, tx['body'], signature)
print(f"서명 유효: {is_valid}")
```

## 💡 주요 기능

### 1. **작업 증명 (PoW)**
- 난이도에 맞는 해시를 찾을 때까지 nonce 증가
- 난이도가 1 증가할 때마다 작업량 2배 증가

### 2. **Most-Work 체인 선택**
- 가장 많은 작업량이 누적된 체인을 메인 체인으로 선택
- 더 무거운 체인이 나타나면 자동으로 전환 (Reorg)

### 3. **고아 블록 처리**
- 부모가 아직 도착하지 않은 블록을 대기실에 보관
- 부모 블록 도착 시 자동으로 연결 시도

### 4. **상태 관리 (Replay)**
- 제네시스부터 현재 팁까지 모든 트랜잭션을 다시 재생
- Undo Log 없이 상태 재구성

### 5. **난이도 자동 조정**
- 3블록마다 난이도 자동 조정
- 목표 블록 시간(2초)에 맞춰 난이도 증가/감소

### 6. **디지털 서명 (ECDSA)** 🆕
- **secp256k1 곡선** 사용 (비트코인과 동일)
- **트랜잭션 서명**: 개인키로 트랜잭션에 서명
- **서명 검증**: 공개키로 서명 유효성 확인
- **주소 생성**: 공개키 → SHA-256 → 주소
- **위조 방지**: 서명 없거나 무효한 서명은 블록 거부

### 7. **트랜잭션 검증 강화**
- 잔액 확인
- Nonce 기반 리플레이 공격 방지
- **디지털 서명 검증** (새로 추가)
- 공개키-주소 일치 확인
- 코인베이스 보상 검증

## 🔍 기존 코드와의 차이점

### 모듈화 장점:
1. **관심사 분리**: 각 클래스가 독립된 파일로 분리되어 유지보수 용이
2. **재사용성**: 각 모듈을 다른 프로젝트에서도 import하여 사용 가능
3. **테스트 용이성**: 각 모듈을 독립적으로 테스트 가능
4. **가독성**: 파일이 작아져서 코드 이해가 쉬움
5. **확장성**: 새로운 기능 추가 시 해당 모듈만 수정

### 기존 단일 파일 (consensus_simulator.py):
- 모든 클래스가 한 파일에 있어 667줄의 긴 코드
- 수정 시 전체 파일을 열어야 함

### 모듈화 버전:
- 각 파일이 100-600줄로 분리
- 필요한 모듈만 import하여 사용
- 각 모듈이 명확한 책임을 가짐

## ⚙️ 설정 변경

`config.py`에서 시뮬레이션 파라미터 조정 가능:

```python
# 난이도 조절 주기 변경
ADJUSTMENT_INTERVAL = 5  # 5블록마다 조정

# 목표 블록 시간 변경
TARGET_BLOCK_TIME = 3  # 3초

# 채굴 확률 변경
MINING_PROBABILITY = 0.5  # 50%
```

## 📊 시뮬레이션 출력 예시

```
[START] 시뮬레이션 시작 (Genesis Hash: 00a3f2)

--- Time: 1 ---
[MINE]  [Alice] 블록 채굴 성공! (Work: 8)
[EXTEND] [Bob] 체인 연장: 3f5a21 (H:1)
   Node[Alice]: Tip=3f5a21(H:1, Work:8) | Bal={'balance': 50, 'nonce': 0}
   Node[Bob]: Tip=3f5a21(H:1, Work:8) | Bal={'balance': 0, 'nonce': 0}

--- Time: 2 ---
[MINE]  [Bob] 블록 채굴 성공! (Work: 16)
[EXTEND] [Alice] 체인 연장: 7b2c43 (H:2)
   Node[Alice]: Tip=7b2c43(H:2, Work:16) | Bal={'balance': 50, 'nonce': 0}
   Node[Bob]: Tip=7b2c43(H:2, Work:16) | Bal={'balance': 50, 'nonce': 0}
```

## 🎓 학습 포인트

이 시뮬레이터를 통해 학습할 수 있는 블록체인 핵심 개념:

1. **분산 합의**: 여러 노드가 동일한 체인에 합의하는 과정
2. **포크 해결**: Most-work 규칙으로 갈라진 체인 중 하나 선택
3. **이중 지불 방지**: Nonce 기반 트랜잭션 순서 보장
4. **난이도 조정**: 네트워크 해시파워 변화에 대응
5. **고아 블록 처리**: 네트워크 지연 상황 처리
6. **체인 재구성**: 더 무거운 체인으로 전환

## 📝 라이선스

교육용 프로젝트
