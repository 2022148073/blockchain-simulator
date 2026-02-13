"""
시나리오 7: Orphan 블록

부모 없이 도착한 블록은 orphan_pool에 저장되었다가
부모 수신 후 올바른 parent state 기준으로 재검증
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, Block, config


def test_orphan_blocks():
    """Orphan 블록 처리 테스트"""
    print("[TEST] 시나리오: Orphan 블록 처리")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")

    network.register_wallet(wallet_alice)

    node = Node(wallet_alice.address, network.genesis_block)

    # 블록 체인 생성 (node에서)
    print("\n1. 블록 체인 생성")
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)

    config.SIM_TIME = 2
    block2 = node.try_mine()
    # block2는 node에 전달하지 않음

    config.SIM_TIME = 3
    block3 = Block(
        index=block2.index + 1,
        timestamp=config.SIM_TIME,
        transactions=[{"body": {"sender": "SYSTEM", "recipient": wallet_alice.address, "amount": 50, "nonce": 0}, "sig": None}],
        difficulty=block2.difficulty,
        previous_hash=block2.hash,
        miner_id=wallet_alice.address
    )
    block3.total_work = block2.total_work + block3.block_work
    block3.mine_block()

    # block3을 먼저 수신 (부모 block2 없음)
    print("\n2. Orphan 블록 수신 (부모 미수신)")
    initial_tip = node.get_tip_block().hash
    node.receive_block(copy.deepcopy(block3))

    current_tip = node.get_tip_block().hash
    orphan_count = sum(len(v) for v in node.orphan_pool.values())

    print(f"   Tip 변경 여부: {initial_tip[:8]}... == {current_tip[:8]}... : {initial_tip == current_tip}")
    print(f"   Orphan pool 크기: {orphan_count}")

    assert initial_tip == current_tip, "Tip should not change (orphan)"
    assert orphan_count == 1, "block3 should be in orphan pool"
    assert block2.hash in node.orphan_pool, "Orphan should be indexed by parent hash"

    # 부모 블록(block2) 수신
    print("\n3. 부모 블록 수신")
    node.receive_block(copy.deepcopy(block2))

    new_tip = node.get_tip_block()
    orphan_count_after = sum(len(v) for v in node.orphan_pool.values())

    print(f"   새 Tip: Block #{new_tip.index} ({new_tip.hash[:8]}...)")
    print(f"   Orphan pool 크기: {orphan_count_after}")

    # 검증: block3이 자동으로 연결됨
    assert new_tip.hash == block3.hash, "block3 should be new tip"
    assert orphan_count_after == 0, "Orphan pool should be empty"
    assert new_tip.index == 3, "Chain height should be 3"

    # 상태도 올바르게 재구성되었는지 확인
    alice_state = node.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    expected_balance = 50 + 50 + 50  # 3번 채굴

    print(f"\n4. 최종 상태")
    print(f"   Alice 잔액: {alice_state['balance']}")
    print(f"   체인 높이: {new_tip.index}")

    assert alice_state['balance'] == expected_balance, f"Alice should have {expected_balance}"

    print("\n[OK] 시나리오 7 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_orphan_blocks()
        print("\n[OK] Orphan Blocks Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
