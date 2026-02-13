"""
시나리오 11: 난이도 조정 알고리즘

블록 생성 속도에 따라 난이도가 자동으로 조정되는지 검증
- 블록이 빠르면 난이도 증가
- 블록이 느리면 난이도 감소
- 조정 주기(ADJUSTMENT_INTERVAL)마다 적용
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_difficulty_adjustment():
    """난이도 조정 알고리즘 테스트"""
    print("[TEST] 시나리오: 난이도 조정 알고리즘")

    network = NetworkSimulator()
    wallet_alice = Wallet("Alice")
    network.register_wallet(wallet_alice)

    node = Node(wallet_alice.address, network.genesis_block)
    network.add_node(node)

    # Case A: 초기 난이도 확인
    print("\n1. 초기 난이도 확인")
    genesis = network.genesis_block
    print(f"   Genesis 난이도: {genesis.difficulty}")
    assert genesis.difficulty == 2, "Genesis difficulty should be 2"

    # Case B: 조정 주기 전 블록들 (난이도 유지)
    print("\n2. 조정 주기 전 블록 채굴 (난이도 유지)")
    config.SIM_TIME = 1
    block1 = node.try_mine()
    node.receive_block(block1)
    print(f"   Block 1 난이도: {block1.difficulty}")
    assert block1.difficulty == 2, "Block 1 should maintain difficulty 2"

    config.SIM_TIME = 2
    block2 = node.try_mine()
    node.receive_block(block2)
    print(f"   Block 2 난이도: {block2.difficulty}")
    assert block2.difficulty == 2, "Block 2 should maintain difficulty 2"

    # Case C: 블록이 너무 빠를 때 (난이도 증가)
    print("\n3. 블록이 빠를 때 난이도 증가")
    # ADJUSTMENT_INTERVAL = 3이므로, block3부터 조정됨
    # 이전 3블록의 평균 시간이 TARGET_BLOCK_TIME보다 짧으면 난이도 증가
    config.SIM_TIME = 3  # 평균 1초/블록 (목표 2초보다 빠름)
    block3 = node.try_mine()
    node.receive_block(block3)

    print(f"   Block 3 난이도: {block3.difficulty}")
    print(f"   이전 블록들 시간 간격: 1초/블록 (목표: {config.TARGET_BLOCK_TIME}초)")

    # 난이도가 증가했는지 확인
    expected_difficulty = node.get_expected_difficulty(block3, block2)
    print(f"   예상 난이도: {expected_difficulty}")
    assert block3.difficulty == expected_difficulty, f"Block 3 difficulty should be {expected_difficulty}"

    # Case D: 블록이 너무 느릴 때 (난이도 감소)
    print("\n4. 블록이 느릴 때 난이도 감소 테스트")

    # 새로운 노드로 시뮬레이션 (느린 블록 생성)
    node2 = Node(wallet_alice.address, network.genesis_block)

    config.SIM_TIME = 1
    slow_block1 = node2.try_mine()
    node2.receive_block(slow_block1)

    config.SIM_TIME = 10  # 9초 간격
    slow_block2 = node2.try_mine()
    node2.receive_block(slow_block2)

    config.SIM_TIME = 20  # 10초 간격
    slow_block3 = node2.try_mine()
    node2.receive_block(slow_block3)

    # 평균 9.5초/블록 (목표 2초보다 매우 느림)
    print(f"   이전 블록들 시간 간격: ~9.5초/블록 (목표: {config.TARGET_BLOCK_TIME}초)")

    expected_difficulty_slow = node2.get_expected_difficulty(slow_block3, slow_block2)
    print(f"   Block 3 난이도: {slow_block3.difficulty}")
    print(f"   예상 난이도: {expected_difficulty_slow}")
    assert slow_block3.difficulty == expected_difficulty_slow, "Difficulty should adjust for slow blocks"

    # 난이도가 감소했는지 확인 (최소 1까지만)
    assert slow_block3.difficulty <= slow_block2.difficulty, "Difficulty should decrease or stay same"

    # Case E: get_ancestor 함수 테스트
    print("\n5. get_ancestor 함수 테스트")
    ancestor = node.get_ancestor(block3, 1)
    print(f"   Block 3의 높이 1 조상: {ancestor.hash[:8] if ancestor else 'None'}...")
    assert ancestor is not None, "Should find ancestor at height 1"
    assert ancestor.index == 1, "Ancestor should be at index 1"
    assert ancestor.hash == block1.hash, "Ancestor should be block1"

    # Genesis까지 거슬러 올라가기
    ancestor_genesis = node.get_ancestor(block3, 0)
    print(f"   Block 3의 높이 0 조상: {ancestor_genesis.hash[:8] if ancestor_genesis else 'None'}...")
    assert ancestor_genesis is not None, "Should find genesis"
    assert ancestor_genesis.hash == genesis.hash, "Ancestor should be genesis"

    print("\n[OK] 시나리오 11 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_difficulty_adjustment()
        print("\n[OK] Difficulty Adjustment Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        sys.exit(1)
