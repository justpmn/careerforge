
from src.preprocessing.competency_evidence_extractor import (
    extract_competency_evidence,
)


TEST_CASES = {
    "mobile_developer": {
        "text": (
            "Built a Flutter mobile app using the Android SDK. "
            "Developed mobile UI with Jetpack Compose. "
            "Performed mobile app testing and deployed through "
            "Google Play Console."
        ),
        "expected": [
            "mobile_app_development",
            "mobile_ui",
            "mobile_platform_integration",
            "mobile_testing",
            "mobile_release",
        ],
    },

    "embedded_developer": {
        "text": (
            "Developed embedded firmware for ESP32 microcontrollers. "
            "Implemented SPI and UART communication using FreeRTOS. "
            "Performed JTAG firmware debugging and "
            "hardware-in-the-loop testing."
        ),
        "expected": [
            "embedded_firmware",
            "embedded_microcontrollers",
            "embedded_interfaces",
            "embedded_real_time",
            "embedded_debugging",
            "embedded_testing",
        ],
    },

    "game_developer": {
        "text": (
            "Built a game using Unity with game mechanics, "
            "level design, collision detection and shaders. "
            "Performed frame-rate optimization and playtesting."
        ),
        "expected": [
            "game_engine",
            "gameplay_programming",
            "game_design",
            "game_physics",
            "game_rendering",
            "game_optimization",
            "game_testing",
        ],
    },
}


def main():
    for career, case in TEST_CASES.items():

        print(f"\n{'=' * 55}")
        print(f"CAREER: {career}")
        print("=" * 55)

        result = extract_competency_evidence(
            case["text"]
        )

        for competency in case["expected"]:

            matches = result.get(competency, [])

            assert matches, (
                f"{career}: Missing evidence "
                f"for {competency}"
            )

            print(
                f"PASS: {competency} "
                f"-> {matches[0]['matched_phrase']}"
            )

        print(
            f"\n{career}: "
            f"{len(case['expected'])} checks passed"
        )

    print("\nALL SPECIALIST EVIDENCE TESTS PASSED")


if __name__ == "__main__":
    main()
