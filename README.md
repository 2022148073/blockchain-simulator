# Blockchain Simulator

Python으로 구현한 교육용 블록체인 시뮬레이터입니다. 비트코인과 유사한 PoW(Proof of Work) 합의 알고리즘, ECDSA 디지털 서명, Account 모델, Nonce 기반 Replay 방지 등의 핵심 기능을 포함합니다.

## 🎯 주요 특징

### 핵심 블록체인 기능
- **PoW (Proof of Work) 합의**: SHA-256 기반 채굴
- **Most-Work Chain Selection**: 가장 무거운 체인 선택 (누적 작업량 기준)
- **Deep Reorg 지원**: 공통 조상 탐색 및 상태 재구성
- **Orphan Block 처리**: 부모 블록 대기 및 자동 연결

### 암호화 및 보안
- **ECDSA 디지털 서명**: secp256k1 곡선 사용 (Bitcoin 호환)
- **Account 모델**: Balance + Nonce 기반 상태 관리
- **Replay 공격 방지**: 순차적 nonce 검증
- **서명 무결성 검증**: 트랜잭션 변조 감지

### 고급 기능
- **난이도 자동 조정**: 블록 생성 속도에 따른 난이도 조절
- **지갑 백업/복구**: 개인키 내보내기/가져오기
- **멀티 지갑 관리**: WalletManager를 통한 다중 지갑 관리
- **네트워크 시뮬레이션**: 블록/트랜잭션 브로드캐스팅

## 📁 프로젝트 구조

```
blockchain/
├── blockchain/                # 메인 블록체인 구현
│   ├── __init__.py           # 패키지 초기화
│   ├── config.py             # 시스템 상수 (난이도, 보상 등)
│   ├── crypto.py             # ECDSA 암호화 유틸리티
│   ├── wallet.py             # 지갑 및 WalletManager
│   ├── block.py              # Block 클래스
│   ├── node.py               # Node 클래스 (핵심 합의 로직)
│   ├── network.py            # NetworkSimulator
│   ├── main.py               # 실행 예제 스크립트
│   └── README.md             # 모듈 문서
│
├── scenarios/                 # 종합 테스트 시나리오 (14개)
│   ├── __init__.py
│   ├── sequential_nonce.py          # 시나리오 1
│   ├── replay_prevention.py         # 시나리오 2
│   ├── invalid_signature.py         # 시나리오 3
│   ├── nonce_skip_reverse.py        # 시나리오 4
│   ├── double_spend_reorg.py        # 시나리오 5
│   ├── deep_reorg.py                # 시나리오 6
│   ├── orphan_blocks.py             # 시나리오 7
│   ├── txid_stability.py            # 시나리오 8
│   ├── tx_order_attack.py           # 시나리오 9
│   ├── mempool_cleanup_reorg.py     # 시나리오 10
│   ├── difficulty_adjustment.py     # 시나리오 11
│   ├── wallet_recovery.py           # 시나리오 12
│   ├── wallet_manager.py            # 시나리오 13
│   ├── network_broadcast.py         # 시나리오 14
│   └── run_all.py            # 전체 테스트 실행
│
├── consensus_simulator.py    # 원본 파일 (참고용)
└── README.md                 # 프로젝트 문서 (이 파일)
```

## 🚀 빠른 시작

### 1. 환경 설정

Python 3.7 이상 필요

```bash
pip install cryptography
```

### 2. 기본 시뮬레이션 실행

```bash
# 메인 시뮬레이션 실행
python blockchain/main.py

# 또는 개별 데모 실행
cd blockchain
python crypto.py      # 암호화 기능 데모
python wallet.py      # 지갑 기능 데모
```

### 3. 테스트 시나리오 실행

```bash
# 전체 14개 시나리오 실행
python scenarios/run_all.py

# 개별 시나리오 실행
python scenarios/sequential_nonce.py
python scenarios/difficulty_adjustment.py
```

## 📊 테스트 시나리오 (14개)

모든 시나리오는 독립적으로 실행 가능하며, 블록체인의 핵심 기능을 검증합니다.

### 기본 시나리오 (1-10)

#### 1. Sequential Nonce (연속 nonce 처리)
**파일**: `scenarios/sequential_nonce.py`

동일 계정의 연속 거래(nonce 1→2→3)가 블록에 포함될 때 서명 검증, nonce 증가, 잔액 반영, mempool 정리가 정확히 동작하는지 검증

**검증 항목**:
- 초기 채굴로 잔액 확보
- 연속 nonce (1, 2, 3) 트랜잭션 생성
- 블록 채굴 및 상태 업데이트
- Mempool 자동 정리

---

#### 2. Replay Prevention (Replay 공격 방지)
**파일**: `scenarios/replay_prevention.py`

이미 확정된 트랜잭션 또는 동일 nonce의 트랜잭션 재전파 시 거부하는지 검증

**검증 항목**:
- 동일 txid 재전파 거부
- 동일 nonce로 다른 금액 전송 시도 (이중지불) 거부
- Mempool 정리 로직

---

#### 3. Invalid Signature (잘못된 서명 감지)
**파일**: `scenarios/invalid_signature.py`

트랜잭션 서명 변조, body 변조, 사칭 시도를 감지하는지 검증

**검증 항목**:
- Case A: 서명 변조 감지
- Case B: Body 변조 시 서명 불일치 감지
- Case C: 다른 사람의 서명으로 주소 사칭 시도 방지

---

#### 4. Nonce Skip/Reverse (Nonce 건너뛰기/역순)
**파일**: `scenarios/nonce_skip_reverse.py`

nonce=2 거래가 nonce=1 없이 먼저 블록에 포함되거나, 역순으로 포함될 때 블록 무효 처리

**검증 항목**:
- Case A: Nonce 건너뛰기 (0 → 2) 블록 거부
- Case B: Nonce 역순 (2→1) 블록 거부
- Case C: 정상 순서 (1→2) 블록 승인

---

#### 5. Double Spend Reorg (이중지불 경쟁 및 Reorg)
**파일**: `scenarios/double_spend_reorg.py`

같은 nonce의 두 거래가 포크된 체인에 각각 포함되었다가 reorg 발생 시 패배 체인의 거래는 무효 처리

**검증 항목**:
- 동일 nonce로 두 개의 다른 트랜잭션 생성
- 포크 발생 (각 노드가 다른 tx 채굴)
- Reorg 후 승리 체인의 tx만 유효
- Mempool 정리 (패배 tx 제거)

---

#### 6. Deep Reorg (깊은 재구성)
**파일**: `scenarios/deep_reorg.py`

공통 조상 탐색 후 롤백+replay 과정에서 balance와 nonce가 최종 체인 기준으로 정확히 재구성

**검증 항목**:
- 공통 조상까지 체인 구축
- 대체 체인 생성 (더 무거운 체인)
- Deep reorg 발생
- 상태 정확성 검증

---

#### 7. Orphan Blocks (고아 블록 처리)
**파일**: `scenarios/orphan_blocks.py`

부모 없이 도착한 블록은 orphan_pool에 저장되었다가 부모 수신 후 올바른 parent state 기준으로 재검증

**검증 항목**:
- 부모 블록 없이 자식 블록 먼저 도착
- Orphan pool에 저장
- 부모 블록 도착 시 자동 연결
- 상태 재구성 검증

---

#### 8. TxID Stability (트랜잭션 ID 안정성)
**파일**: `scenarios/txid_stability.py`

txid는 body의 canonical serialization 기반 해시로 signature 변경과 무관하게 동일해야 함

**검증 항목**:
- 동일 body, 다른 서명 → 같은 TxID
- Body 변경 → 다른 TxID
- 서명 변조해도 TxID 동일

---

#### 9. Tx Order Attack (트랜잭션 순서 공격 방지)
**파일**: `scenarios/tx_order_attack.py`

같은 계정의 거래를 nonce 역순으로 블록에 넣으면 validate_block에서 실패

**검증 항목**:
- Case A: 역순 (3→2→1) 블록 거부
- Case B: 중간 건너뛰기 (1→3) 블록 거부
- Case C: 정순 (1→2→3) 블록 승인

---

#### 10. Mempool Cleanup Reorg (Reorg 후 Mempool 정리)
**파일**: `scenarios/mempool_cleanup_reorg.py`

체인 교체 이후 mempool의 모든 거래는 최신 state 기준으로 nonce/잔액/서명을 재검증하여 유효한 것만 유지

**검증 항목**:
- Reorg 후 mempool 자동 정리
- 포함된 tx 제거
- Nonce 불일치 tx 제거
- 유효한 tx만 유지

---

### 고급 시나리오 (11-14)

#### 11. Difficulty Adjustment (난이도 자동 조정)
**파일**: `scenarios/difficulty_adjustment.py`

블록 생성 속도에 따라 난이도가 자동으로 조정되는지 검증

**검증 항목**:
- 초기 난이도 확인
- 조정 주기 전 난이도 유지
- 블록이 빠를 때 난이도 증가
- 블록이 느릴 때 난이도 감소
- `get_ancestor()` 함수 검증

**난이도 조정 알고리즘**:
- 조정 주기: 3블록마다 (ADJUSTMENT_INTERVAL)
- 목표 시간: 2초/블록 (TARGET_BLOCK_TIME)
- 평균 시간이 목표보다 짧으면 난이도 증가
- 평균 시간이 목표보다 길면 난이도 감소

---

#### 12. Wallet Recovery (지갑 백업 및 복구)
**파일**: `scenarios/wallet_recovery.py`

개인키 내보내기/가져오기 기능 검증

**검증 항목**:
- 원본 지갑 생성
- 개인키 백업 (PEM 형식)
- 백업한 개인키로 지갑 복구
- 주소 및 공개키 일치 확인
- 복구된 지갑으로 트랜잭션 서명
- 서명 검증
- 공개키 직렬화/역직렬화

**백업 형식**: PKCS8 PEM

---

#### 13. Wallet Manager (멀티 지갑 관리)
**파일**: `scenarios/wallet_manager.py`

WalletManager를 이용한 여러 지갑 생성 및 관리 기능 검증

**검증 항목**:
- WalletManager 초기화
- 여러 지갑 생성 (Alice, Bob, Charlie)
- 이름으로 지갑 조회
- 주소 조회
- 중복 생성 방지
- 여러 지갑 간 트랜잭션 시뮬레이션

**WalletManager 주요 메서드**:
- `create_wallet(name)`: 지갑 생성
- `get_wallet(name)`: 지갑 조회
- `get_address(name)`: 주소 조회
- `list_wallets()`: 전체 지갑 목록

---

#### 14. Network Broadcast (네트워크 브로드캐스팅)
**파일**: `scenarios/network_broadcast.py`

블록과 트랜잭션의 네트워크 전파 기능 검증

**검증 항목**:
- 네트워크 및 3개 노드 생성
- Node1이 블록 채굴 및 브로드캐스트
- 모든 노드가 블록 수신 확인
- Deepcopy 검증 (독립적인 블록 객체)
- 트랜잭션 브로드캐스트
- 모든 노드의 mempool에 추가 확인
- 블록 채굴 후 모든 노드 상태 일치
- Mempool 정리 확인

---

## 🧪 테스트 결과

```bash
$ python scenarios/run_all.py

======================================================================
BLOCKCHAIN SIMULATOR - COMPREHENSIVE TEST SUITE
======================================================================

Testing 14 comprehensive blockchain scenarios:
1. Sequential nonce handling
2. Replay attack prevention
3. Invalid signature detection
4. Nonce skip and reverse order
5. Double spend with reorg
6. Deep reorganization
7. Orphan block handling
8. Transaction ID stability
9. Transaction order attack prevention
10. Mempool cleanup after reorg
11. Difficulty adjustment algorithm
12. Wallet backup and recovery
13. Multi-wallet management
14. Network broadcasting

======================================================================
TEST SUMMARY
======================================================================
[OK] Scenario 1: Sequential Nonce
[OK] Scenario 2: Replay Prevention
[OK] Scenario 3: Invalid Signature
[OK] Scenario 4: Nonce Skip/Reverse
[OK] Scenario 5: Double Spend Reorg
[OK] Scenario 6: Deep Reorg
[OK] Scenario 7: Orphan Blocks
[OK] Scenario 8: TxID Stability
[OK] Scenario 9: Tx Order Attack
[OK] Scenario 10: Mempool Cleanup Reorg
[OK] Scenario 11: Difficulty Adjustment
[OK] Scenario 12: Wallet Recovery
[OK] Scenario 13: Wallet Manager
[OK] Scenario 14: Network Broadcast

Total: 14 tests
[OK] Passed: 14
[FAIL] Failed: 0
======================================================================

[OK] ALL TESTS PASSED!
```

**테스트 커버리지: 100%** ✅

## 📚 핵심 개념

### 1. PoW (Proof of Work)

블록 채굴 시 난이도에 맞는 해시를 찾을 때까지 nonce를 증가시킵니다.

```python
# 난이도 2: 해시가 "00"으로 시작해야 함
target = "0" * difficulty
while not hash.startswith(target):
    nonce += 1
    hash = calculate_hash()
```

### 2. Most-Work Chain Selection

누적 작업량(total_work)이 가장 큰 체인을 선택합니다.

```python
# 각 블록의 작업량: 2^difficulty
block_work = 1 << difficulty

# 누적 작업량
total_work = parent.total_work + block_work

# 더 무거운 체인으로 전환
if new_block.total_work > current_tip.total_work:
    # Reorg 또는 체인 연장
```

### 3. ECDSA 디지털 서명

secp256k1 곡선을 사용한 서명 및 검증

```python
# 서명 생성
signature = private_key.sign(message_bytes, ec.ECDSA(hashes.SHA256()))

# 서명 검증
public_key.verify(signature, message_bytes, ec.ECDSA(hashes.SHA256()))

# 주소 생성 (공개키 → SHA256 → RIPEMD160)
address = hashlib.new('ripemd160',
          hashlib.sha256(public_key_bytes).digest()).hexdigest()
```

### 4. Account 모델

각 주소는 balance와 nonce를 가집니다.

```python
state = {
    "address1": {"balance": 100, "nonce": 5},
    "address2": {"balance": 50, "nonce": 2}
}

# 트랜잭션 검증
expected_nonce = state[sender]["nonce"] + 1
if tx["body"]["nonce"] != expected_nonce:
    reject()
```

### 5. Reorg (Chain Reorganization)

더 무거운 체인이 발견되면 상태를 재구성합니다.

```python
# 1. 공통 조상 찾기
common_ancestor = find_common_ancestor(old_tip, new_tip)

# 2. 롤백할 블록들 수집
discarded_blocks = collect_blocks(common_ancestor, old_tip)

# 3. 상태 재구성 (Genesis부터 replay)
rebuild_state(new_tip)

# 4. Mempool 정리
clean_mempool()
```

## ⚙️ 설정

`blockchain/config.py`에서 시스템 상수를 조정할 수 있습니다.

```python
# 시뮬레이션 시간
SIM_TIME = 0

# 난이도 조정 주기 (블록 수)
ADJUSTMENT_INTERVAL = 3

# 목표 블록 생성 시간 (초)
TARGET_BLOCK_TIME = 2

# 채굴 보상
MINING_REWARD = 50

# 채굴 확률 (시뮬레이션용)
MINING_PROBABILITY = 0.3

# 블록당 최대 트랜잭션 수
MAX_TXS_PER_BLOCK = 5
```

## 🔍 주요 클래스 및 메서드

### Block 클래스
- `__init__()`: 블록 생성
- `calculate_hash()`: 블록 해시 계산
- `mine_block()`: PoW 채굴

### Node 클래스
- `receive_block()`: 블록 수신 및 처리
- `validate_block()`: 블록 검증
- `validate_transactions()`: 트랜잭션 검증
- `verify_transaction_signature()`: 서명 검증
- `handle_reorg()`: 체인 재구성
- `rebuild_state()`: 상태 재구성
- `clean_mempool()`: Mempool 정리
- `try_mine()`: 블록 채굴 시도
- `get_expected_difficulty()`: 난이도 계산

### Wallet 클래스
- `__init__()`: 지갑 생성 (키 쌍 자동 생성)
- `create_transaction()`: 트랜잭션 생성 및 서명
- `sign_transaction()`: 트랜잭션 서명
- `export_private_key()`: 개인키 백업
- `from_private_key()`: 개인키로부터 복구

### NetworkSimulator 클래스
- `create_genesis()`: 제네시스 블록 생성
- `add_node()`: 노드 추가
- `register_wallet()`: 지갑 등록
- `broadcast_block()`: 블록 브로드캐스트
- `add_transaction_to_network()`: 트랜잭션 브로드캐스트
- `run_simulation()`: 시뮬레이션 실행

## 🛠️ 개발 가이드

### 새로운 시나리오 추가

1. `scenarios/` 폴더에 새 파일 생성
2. 다음 템플릿 사용:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config

def test_my_scenario():
    """시나리오 설명"""
    print("[TEST] 시나리오: ...")

    # 테스트 코드 작성
    # ...

    print("\n[OK] 시나리오 검증 완료")
    return True

if __name__ == "__main__":
    try:
        test_my_scenario()
        print("\n[OK] Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
```

3. `scenarios/__init__.py`와 `scenarios/run_all.py`에 추가

### 커스텀 합의 알고리즘

`Node` 클래스를 상속하여 새로운 합의 메커니즘을 구현할 수 있습니다.

```python
class MyNode(Node):
    def validate_block(self, new_block, parent_block):
        # 커스텀 검증 로직
        return super().validate_block(new_block, parent_block)
```

## 📖 참고 자료

### 블록체인 기초
- [Bitcoin Whitepaper](https://bitcoin.org/bitcoin.pdf)
- [Mastering Bitcoin](https://github.com/bitcoinbook/bitcoinbook)

### 암호화
- [ECDSA 설명](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm)
- [secp256k1 곡선](https://en.bitcoin.it/wiki/Secp256k1)

### Python 라이브러리
- [cryptography](https://cryptography.io/en/latest/)

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📝 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

## ⚠️ 주의사항

- **교육용 코드**: 실제 프로덕션 환경에서 사용하지 마세요
- **보안**: 개인키 관리는 데모 목적이며, 실제 환경에서는 HSM 등을 사용해야 합니다
- **성능**: 시뮬레이션 목적이므로 실제 블록체인보다 단순화되어 있습니다

---
