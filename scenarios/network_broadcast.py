"""
시나리오 14: 네트워크 브로드캐스팅

블록과 트랜잭션의 네트워크 전파 기능 검증
- 블록 브로드캐스트 (모든 노드에 전파)
- 트랜잭션 브로드캐스트
- 각 노드가 독립적인 복사본을 받는지 확인 (deepcopy)
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Node, NetworkSimulator, Wallet, config


def test_network_broadcast():
    """네트워크 브로드캐스팅 테스트"""
    print("[TEST] 시나리오: 네트워크 브로드캐스팅")

    # Case A: 네트워크 및 여러 노드 생성
    print("\n1. 네트워크 및 3개 노드 생성")
    network = NetworkSimulator()

    wallet_alice = Wallet("Alice")
    wallet_bob = Wallet("Bob")
    wallet_charlie = Wallet("Charlie")

    network.register_wallet(wallet_alice)
    network.register_wallet(wallet_bob)
    network.register_wallet(wallet_charlie)

    node1 = Node(wallet_alice.address, network.genesis_block)
    node2 = Node(wallet_bob.address, network.genesis_block)
    node3 = Node(wallet_charlie.address, network.genesis_block)

    network.add_node(node1)
    network.add_node(node2)
    network.add_node(node3)

    print(f"   네트워크 노드 수: {len(network.nodes)}")
    assert len(network.nodes) == 3, "Network should have 3 nodes"

    # Case B: Node1이 블록 채굴 후 브로드캐스트
    print("\n2. Node1이 블록 채굴 및 브로드캐스트")
    config.SIM_TIME = 1
    block1 = node1.try_mine()

    # 자기 자신에게 먼저 적용
    node1.receive_block(block1)

    # 네트워크에 브로드캐스트
    network.broadcast_block(node1, block1)

    # 모든 노드가 블록을 받았는지 확인
    print(f"   Node1 tip index: {node1.get_tip_block().index}")
    print(f"   Node2 tip index: {node2.get_tip_block().index}")
    print(f"   Node3 tip index: {node3.get_tip_block().index}")

    assert node1.get_tip_block().index == 1, "Node1 should have block1"
    assert node2.get_tip_block().index == 1, "Node2 should have block1"
    assert node3.get_tip_block().index == 1, "Node3 should have block1"

    # 모든 노드의 tip hash가 같은지 확인
    assert node1.get_tip_block().hash == block1.hash, "Node1 tip should be block1"
    assert node2.get_tip_block().hash == block1.hash, "Node2 tip should be block1"
    assert node3.get_tip_block().hash == block1.hash, "Node3 tip should be block1"

    # Case C: deepcopy 확인 (각 노드가 독립적인 블록 객체를 가지는지)
    print("\n3. Deepcopy 검증 (각 노드의 블록 객체 독립성)")
    block1_node1 = node1.block_index[block1.hash]
    block1_node2 = node2.block_index[block1.hash]
    block1_node3 = node3.block_index[block1.hash]

    # 객체 ID가 다른지 확인 (다른 메모리 주소)
    print(f"   Node1 block1 id: {id(block1_node1)}")
    print(f"   Node2 block1 id: {id(block1_node2)}")
    print(f"   Node3 block1 id: {id(block1_node3)}")

    assert id(block1_node1) != id(block1_node2), "Nodes should have different block objects"
    assert id(block1_node2) != id(block1_node3), "Nodes should have different block objects"
    assert id(block1_node1) != id(block1_node3), "Nodes should have different block objects"

    # 하지만 내용은 같아야 함
    assert block1_node1.hash == block1_node2.hash == block1_node3.hash, "Block hashes should match"

    # Case D: 트랜잭션 브로드캐스트
    print("\n4. 트랜잭션 네트워크 브로드캐스트")

    # Alice가 Bob에게 송금하는 트랜잭션 생성 및 브로드캐스트
    network.add_transaction_to_network(wallet_alice.address, wallet_bob.address, 10)

    # 모든 노드의 mempool에 트랜잭션이 추가되었는지 확인
    print(f"   Node1 mempool 크기: {len(node1.mempool)}")
    print(f"   Node2 mempool 크기: {len(node2.mempool)}")
    print(f"   Node3 mempool 크기: {len(node3.mempool)}")

    assert len(node1.mempool) == 1, "Node1 should have 1 transaction"
    assert len(node2.mempool) == 1, "Node2 should have 1 transaction"
    assert len(node3.mempool) == 1, "Node3 should have 1 transaction"

    # 트랜잭션 내용 확인
    tx_node1 = node1.mempool[0]
    tx_node2 = node2.mempool[0]
    tx_node3 = node3.mempool[0]

    assert tx_node1['body']['sender'] == wallet_alice.address, "Sender should be Alice"
    assert tx_node1['body']['recipient'] == wallet_bob.address, "Recipient should be Bob"
    assert tx_node1['body']['amount'] == 10, "Amount should be 10"

    # 각 노드가 독립적인 트랜잭션 객체를 가지는지 확인
    assert id(tx_node1) != id(tx_node2), "Transactions should be different objects"
    assert id(tx_node2) != id(tx_node3), "Transactions should be different objects"

    # Case E: Node2가 블록 채굴 및 브로드캐스트
    print("\n5. Node2가 블록 채굴 (트랜잭션 포함)")
    config.SIM_TIME = 2
    block2 = node2.try_mine()
    node2.receive_block(block2)

    # 브로드캐스트
    network.broadcast_block(node2, block2)

    # 모든 노드가 블록2를 받았는지 확인
    print(f"   Node1 tip index: {node1.get_tip_block().index}")
    print(f"   Node2 tip index: {node2.get_tip_block().index}")
    print(f"   Node3 tip index: {node3.get_tip_block().index}")

    assert node1.get_tip_block().index == 2, "Node1 should have block2"
    assert node2.get_tip_block().index == 2, "Node2 should have block2"
    assert node3.get_tip_block().index == 2, "Node3 should have block2"

    # Case F: 모든 노드의 상태 일치 확인
    print("\n6. 모든 노드의 상태 일치 확인")
    alice_state_node1 = node1.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    alice_state_node2 = node2.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})
    alice_state_node3 = node3.state.get(wallet_alice.address, {'balance': 0, 'nonce': 0})

    bob_state_node1 = node1.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})
    bob_state_node2 = node2.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})
    bob_state_node3 = node3.state.get(wallet_bob.address, {'balance': 0, 'nonce': 0})

    print(f"   Node1 - Alice: balance={alice_state_node1['balance']}, nonce={alice_state_node1['nonce']}")
    print(f"   Node2 - Alice: balance={alice_state_node2['balance']}, nonce={alice_state_node2['nonce']}")
    print(f"   Node3 - Alice: balance={alice_state_node3['balance']}, nonce={alice_state_node3['nonce']}")

    # 모든 노드의 Alice 상태가 동일한지 확인
    assert alice_state_node1['balance'] == alice_state_node2['balance'] == alice_state_node3['balance'], \
        "Alice balance should be same across all nodes"
    assert alice_state_node1['nonce'] == alice_state_node2['nonce'] == alice_state_node3['nonce'], \
        "Alice nonce should be same across all nodes"

    # Bob 상태 확인
    assert bob_state_node1['balance'] == bob_state_node2['balance'] == bob_state_node3['balance'], \
        "Bob balance should be same across all nodes"

    print(f"   Node1 - Bob: balance={bob_state_node1['balance']}")
    print(f"   Node2 - Bob: balance={bob_state_node2['balance']}")
    print(f"   Node3 - Bob: balance={bob_state_node3['balance']}")

    # Case G: Mempool이 모든 노드에서 비워졌는지 확인
    print("\n7. 블록 채굴 후 Mempool 정리 확인")
    print(f"   Node1 mempool 크기: {len(node1.mempool)}")
    print(f"   Node2 mempool 크기: {len(node2.mempool)}")
    print(f"   Node3 mempool 크기: {len(node3.mempool)}")

    assert len(node1.mempool) == 0, "Node1 mempool should be empty"
    assert len(node2.mempool) == 0, "Node2 mempool should be empty"
    assert len(node3.mempool) == 0, "Node3 mempool should be empty"

    print("\n[OK] 시나리오 14 검증 완료")
    return True


if __name__ == "__main__":
    try:
        test_network_broadcast()
        print("\n[OK] Network Broadcast Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
