"""
블록체인 시뮬레이터 설정 파일
시스템 상수 및 전역 변수 정의
"""

# 전역 시뮬레이션 시간
SIM_TIME = 0

# 시스템 상수 설정
ADJUSTMENT_INTERVAL = 3  # 난이도 조절 주기 (3개 블록마다 조정)
TARGET_BLOCK_TIME = 2    # 목표 블록 생성 시간 (2초)
MAX_STEP = 1             # 난이도 조절 최대 크기 (+1/-1까지 조정 가능)
FUTURE_DRIFT = 36        # 미래 시간 제한
MAX_TIME_JUMP = 6        # 블록당 최대 시간 점프 (6초)

# 채굴 관련 설정
MINING_REWARD = 50       # 채굴 보상 금액
DEFAULT_DIFFICULTY = 2   # 초기 난이도

# 트랜잭션 관련 설정
MAX_TXS_PER_BLOCK = 5    # 블록당 최대 트랜잭션 수

# 네트워크 시뮬레이션 설정
MINING_PROBABILITY = 0.3  # 각 스텝마다 채굴 시도 확률 (30%)
