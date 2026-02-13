"""
시나리오 9: 블록 내 tx 순서 공격

같은 계정의 거래를 nonce 역순으로 블록에 넣으면 validate_block에서 실패
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, Block, config


def test_block_tx_order_attack():
    """블록 내 트랜잭션 순서 공격 테스트"""
    print("[TEST] 시나리오: 블록 내 트랜잭션 순서 공격")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)

    # 초기 채굴
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    # 순차 트랜잭션 생성
    print("\n1. 순차 트랜잭션 생성 (nonce 1, 2, 3)")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 10, 1)
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 5, 2)
    tx3 = wallet_alice.create_transaction(wallet_bob.address, 3, 3)

    tip = node.get_tip_block()
    coinbase = {"body": {"sender": "SYSTEM", "recipient": wallet_alice.address, "amount": 50, "nonce": 0}, "sig": None}

    # Case A: 역순 (3→2→1)
    print("\n2. Case A: 역순 블록 (3→2→1)")
    config.SIM_TIME = 2
    bad_block1 = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[coinbase, tx3, tx2, tx1],  # 역순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block1.mine_block()

    is_valid = node.validate_block(bad_block1, tip)
    print(f"   역순 블록 검증: {is_valid}")
    assert not is_valid, "Reverse order block should be invalid"

    # Case B: 중간 건너뛰기 (1→3, 2 빠짐)
    print("\n3. Case B: 중간 건너뛰기 (1→3)")
    config.SIM_TIME = 3
    bad_block2 = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[coinbase, tx1, tx3],  # tx2 빠짐
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block2.mine_block()

    is_valid = node.validate_block(bad_block2, tip)
    print(f"   중간 건너뛰기 블록 검증: {is_valid}")
    assert not is_valid, "Block with skipped nonce should be invalid"

    # Case C: 정순 (1→2→3)
    print("\n4. Case C: 정순 블록 (1→2→3)")
    config.SIM_TIME = 4
    good_block = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[coinbase, tx1, tx2, tx3],  # 정순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    good_block.mine_block()

    is_valid = node.validate_block(good_block, tip)
    print(f"   정순 블록 검증: {is_valid}")
    assert is_valid, "Block with correct order should be valid"

    print("\n[OK] 시나리오 9 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_block_tx_order_attack()
        print("\n[OK] Tx Order Attack Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
