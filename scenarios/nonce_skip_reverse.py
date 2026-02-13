"""
시나리오 4: Nonce 건너뛰기/역순

nonce=2 거래가 nonce=1 없이 먼저 블록에 포함되면 블록 무효 처리
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, Block, config


def test_nonce_skip_reverse():
    """Nonce 건너뛰기 및 역순 처리 테스트"""
    print("[TEST] 시나리오: Nonce 건너뛰기 및 역순 처리")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)

    node = Node(wallet_alice.address, network.genesis_block)
    network.add_node(node)

    # 초기 채굴
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    # Case A: Nonce 건너뛰기 (0 → 2, 1 건너뜀)
    print("\n1. Case A: Nonce 건너뛰기 (nonce 2, 1 없이)")
    tx_skip = wallet_alice.create_transaction(wallet_bob.address, 10, 2)  # nonce 1 건너뜀

    # 블록 수동 생성
    tip = node.get_tip_block()
    coinbase_tx = {"body": {"sender": "SYSTEM", "recipient": wallet_alice.address, "amount": 50, "nonce": 0}, "sig": None}

    bad_block = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME + 1,
        transactions=[coinbase_tx, tx_skip],
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block.mine_block()

    # 블록 검증
    is_valid = node.validate_block(bad_block, tip)
    print(f"   Nonce 건너뛰기 블록 검증: {is_valid}")
    assert not is_valid, "Block with skipped nonce should be invalid"

    # Case B: Nonce 역순 (nonce 2, 1 순서로)
    print("\n2. Case B: Nonce 역순 (2→1)")
    tx1 = wallet_alice.create_transaction(wallet_bob.address, 5, 1)
    tx2 = wallet_alice.create_transaction(wallet_bob.address, 3, 2)

    # 역순으로 블록에 포함
    config.SIM_TIME = 2
    bad_block2 = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME + 1,
        transactions=[coinbase_tx, tx2, tx1],  # 역순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    bad_block2.mine_block()

    is_valid = node.validate_block(bad_block2, tip)
    print(f"   Nonce 역순 블록 검증: {is_valid}")
    assert not is_valid, "Block with reversed nonce should be invalid"

    # Case C: 정상 순서 (1→2)
    print("\n3. Case C: 정상 순서 (1→2)")
    config.SIM_TIME = 3
    good_block = Block(
        index=tip.index + 1,
        timestamp=config.SIM_TIME + 1,
        transactions=[coinbase_tx, tx1, tx2],  # 정순!
        difficulty=tip.difficulty,
        previous_hash=tip.hash,
        miner_id=wallet_alice.address
    )
    good_block.mine_block()

    is_valid = node.validate_block(good_block, tip)
    print(f"   정상 순서 블록 검증: {is_valid}")
    assert is_valid, "Block with correct nonce order should be valid"

    print("\n[OK] 시나리오 4 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_nonce_skip_reverse()
        print("\n[OK] Nonce Skip/Reverse Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
