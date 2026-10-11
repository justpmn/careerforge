from copy import deepcopy


COMMON_COMPETENCIES = {
    "version_control": {
        "key": "version_control",
        "name": "Version control",
        "level": "core",
        "any_of": ["Git"],
    },

    "testing": {
        "key": "testing",
        "name": "Automated testing",
        "level": "core",
        "assessment": "manual_review",
        "any_of": [],
    },

    "ci_cd": {
        "key": "ci_cd",
        "name": "Continuous integration and delivery",
        "level": "supporting",
        "assessment": "manual_review",
        "any_of": [],
    },

    "cloud_platform": {
        "key": "cloud_platform",
        "name": "Cloud platform experience",
        "level": "supporting",
        "any_of": [
            "Amazon Web Services (AWS)",
            "Microsoft Azure",
            "Google Cloud",
        ],
    },

    "containers": {
        "key": "containers",
        "name": "Containerization",
        "level": "supporting",
        "any_of": ["Docker"],
    },
}


def get_common_groups(*keys):
    """
    Return independent copies of shared
    competency definitions.
    """
    return [
        deepcopy(COMMON_COMPETENCIES[key])
        for key in keys
    ]