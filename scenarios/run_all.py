"""
Run All Test Scenarios

This script runs all 10 blockchain test scenarios and provides a summary report.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scenarios import (
    test_sequential_nonce,
    test_replay_prevention,
    test_invalid_signature,
    test_nonce_skip_reverse,
    test_double_spend_reorg,
    test_deep_reorg,
    test_orphan_blocks,
    test_txid_stability,
    test_block_tx_order_attack,
    test_mempool_cleanup_after_reorg,
    test_difficulty_adjustment,
    test_wallet_recovery,
    test_wallet_manager,
    test_network_broadcast
)


class TestRunner:
    """Test runner for all scenarios"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []

    def run_test(self, test_name, test_func):
        """Run a single test and record the result"""
        print(f"\n{'=' * 70}")
        print(f"Running: {test_name}")
        print('=' * 70)

        try:
            test_func()
            self.passed += 1
            self.test_results.append((test_name, "PASS"))
            print(f"\n[OK] {test_name} - PASSED")
        except AssertionError as e:
            self.failed += 1
            self.test_results.append((test_name, f"FAIL: {e}"))
            print(f"\n[FAIL] {test_name} - FAILED")
            print(f"   Error: {e}")
        except Exception as e:
            self.failed += 1
            self.test_results.append((test_name, f"ERROR: {e}"))
            print(f"\n[FAIL] {test_name} - ERROR")
            print(f"   Exception: {e}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n\n{'=' * 70}")
        print("TEST SUMMARY")
        print('=' * 70)

        for test_name, result in self.test_results:
            status = "[OK]" if result == "PASS" else "[FAIL]"
            print(f"{status} {test_name}")
            if result != "PASS":
                print(f"     {result}")

        print(f"\nTotal: {len(self.test_results)} tests")
        print(f"[OK] Passed: {self.passed}")
        print(f"[FAIL] Failed: {self.failed}")
        print('=' * 70)

        if self.passed == len(self.test_results):
            print("\n[OK] ALL TESTS PASSED!")
        else:
            print(f"\n[FAIL] {self.failed} test(s) failed")


def main():
    """Main entry point"""
    runner = TestRunner()

    print("=" * 70)
    print("BLOCKCHAIN SIMULATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\nTesting 14 comprehensive blockchain scenarios:")
    print("1. Sequential nonce handling")
    print("2. Replay attack prevention")
    print("3. Invalid signature detection")
    print("4. Nonce skip and reverse order")
    print("5. Double spend with reorg")
    print("6. Deep reorganization")
    print("7. Orphan block handling")
    print("8. Transaction ID stability")
    print("9. Transaction order attack prevention")
    print("10. Mempool cleanup after reorg")
    print("11. Difficulty adjustment algorithm")
    print("12. Wallet backup and recovery")
    print("13. Multi-wallet management")
    print("14. Network broadcasting")

    # Run all tests
    runner.run_test("Scenario 1: Sequential Nonce", test_sequential_nonce)
    runner.run_test("Scenario 2: Replay Prevention", test_replay_prevention)
    runner.run_test("Scenario 3: Invalid Signature", test_invalid_signature)
    runner.run_test("Scenario 4: Nonce Skip/Reverse", test_nonce_skip_reverse)
    runner.run_test("Scenario 5: Double Spend Reorg", test_double_spend_reorg)
    runner.run_test("Scenario 6: Deep Reorg", test_deep_reorg)
    runner.run_test("Scenario 7: Orphan Blocks", test_orphan_blocks)
    runner.run_test("Scenario 8: TxID Stability", test_txid_stability)
    runner.run_test("Scenario 9: Tx Order Attack", test_block_tx_order_attack)
    runner.run_test("Scenario 10: Mempool Cleanup Reorg", test_mempool_cleanup_after_reorg)
    runner.run_test("Scenario 11: Difficulty Adjustment", test_difficulty_adjustment)
    runner.run_test("Scenario 12: Wallet Recovery", test_wallet_recovery)
    runner.run_test("Scenario 13: Wallet Manager", test_wallet_manager)
    runner.run_test("Scenario 14: Network Broadcast", test_network_broadcast)

    # Print summary
    runner.print_summary()

    # Return exit code
    return 0 if runner.passed == len(runner.test_results) else 1


if __name__ == "__main__":
    sys.exit(main())
