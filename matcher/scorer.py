import json


class ResumeScorer:
    """Scores resumes against job descriptions using weighted criteria"""

    def __init__(self, config_path: str | None = None):
        """
        Initialize scorer with optional config

        Args:
            config_path: Path to configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.weights = self.config.get(
            "weights",
            {
                "required_skills": 0.5,
                "preferred_skills": 0.25,
                "experience": 0.15,
                "keyword_density": 0.1,
            },
        )

    def _load_config(self, config_path: str | None) -> dict:
        """Load config from file or use defaults"""
        if config_path:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)

            except Exception as e:
                print(f"Error loading config: {e}. Using defaults")

        return {
            "weights": {
                "required_skills": 0.5,
                "preferred_skills": 0.25,
                "experience": 0.15,
                "keyword_density": 0.1,
            },
            "min_score": 0.0,
            "experience_tolerance": 2,
        }

    def score_resume(
        self,
        resume_skills: set[str],
        resume_experience: int,
        resume_keywords: list[str],
        jd_data: dict,
    ) -> dict:
        """
        Calculate match score for a resume against a job description

        Args:
            resume_skills: Set of skills extracted from resume
            resume_experience: years of experiece from resume
            resume_keywords: list of keywords from resume (with duplicates to count)
            jd_data: parsed job description data

        Returns:
            Dictionary with total score and component scores
        """

        jd_required = set(skill.lower() for skill in jd_data.get("required_skills", []))
        jd_preferred = set(
            skill.lower() for skill in jd_data.get("required_skills", [])
        )
        jd_keywords = jd_data.get("keywords", [])
        jd_min_exp = jd_data.get("min_experience", 0)

        required_score = self._calculate_skill_match(resume_skills, jd_required)
        preferred_score = self._calculate_skill_match(resume_skills, jd_preferred)
        experience_score = self._calculate_experience_match(
            resume_experience, jd_min_exp
        )
        keyword_score = self._calculate_keyword_match(resume_keywords, jd_keywords)

        total_score = (
            required_score * self.weights["required_skills"]
            + preferred_score * self.weights["preferred_skills"]
            + experience_score * self.weights["experience"]
            + keyword_score * self.weights["keyword_density"]
        )

        return {
            "total_score": round(total_score * 100, 2),
            "required_skills_score": round(required_score * 100, 2),
            "preferred_skills_score": round(preferred_score * 100, 2),
            "experience_score": round(experience_score * 100, 2),
            "keyword_score": round(keyword_score * 100, 2),
            "matched_required_skills": list(resume_skills & jd_required),
            "matched_preferred_skills": list(resume_skills & jd_preferred),
            "missing_required_skills": list(jd_required - resume_skills),
            "resume_experience": resume_experience,
            "required_experience": jd_min_exp,
        }

    def _calculate_skill_match(
        self, resume_skills: set[str], jd_skills: set[str]
    ) -> float:
        """
        Calculate skill match score (0-1)

        Args:
            resume_skills: Skills from resume
            jd_skills: Required/preferred skills from JD

        Returns:
            Match score between 0 and 1
        """
        if not jd_skills:
            return 1.0

        matched_skills = resume_skills & jd_skills
        match_ratio = len(matched_skills) / len(jd_skills)

        return match_ratio

    def _calculate_experience_match(self, resume_exp: int, required_exp: int) -> float:
        """
        Calculate experience match score (0-1)

        Args:
            resume_exp: years of experience from resume
            required_exp: minimum required years from JD

        Returns:
            Experience match score between 0 and 1
        """
        if required_exp == 0:
            return 1.0

        tolerance = self.config.get("experience_tolerance", 2)

        if resume_exp >= required_exp:
            return 1.0

        if resume_exp >= (required_exp - tolerance):
            gap = required_exp - resume_exp
            score = 1.0 - (gap / (tolerance + 1) * 0.3)
            return max(0.7, score)

        ratio = resume_exp / required_exp if required_exp > 0 else 0
        return max(0.0, ratio * 0.7)

    def _calculate_keyword_match(
        self, resume_keywords: list[str], jd_keywords: list[str]
    ) -> float:
        """
        Calculate keyword density match score (0-1)

        Args:
            resume_keywords: keywords from resume (with frequency)
            jd_keywords: keywords from JD

        Returns:
            Keywords match score between 0 and 1
        """
        if not jd_keywords:
            return 1.0

        resume_keyword_set = set(kw.lower() for kw in resume_keywords)
        jd_keyword_set = set(kw.lower() for kw in jd_keywords)

        matched_keywords = resume_keyword_set & jd_keyword_set

        if not jd_keyword_set:
            return 1.0

        match_ratio = len(matched_keywords) / len(jd_keyword_set)

        frequency_bonus = 0
        if resume_keywords:
            keyword_count = sum(1 for kw in resume_keywords if kw.lower() in jd_keyword_set)
            frequency_bonus = min(0.2, keyword_count / len(resume_keywords))

        return min(1.0, match_ratio + frequency_bonus)

    def rank_resumes(self, scored_resumes: list[dict]) -> list[dict]:
        """
        Rank resumes by total score in descending order

        Args:
            scored_resumes: list of resumes with scores

        Returns:
            sorted list of resumes
        """
        return sorted(scored_resumes, key=lambda x: x['score']['total_score'], reverse=True)

    def filter_by_threshold(self, scored_resumes: list[dict], min_score: float | None = None) -> list[dict]:
        """
        Filter resumes by minimum score threshold

        Args:
            scored_resumes: lit of resumes with scores
            min_score: Minimum score threshold (default from config)

        Returns:
            Filtered list of resumes
        """
        if min_score is None:
            min_score = self.config.get('min_score', 0.0)

        return [r for r in scored_resumes if r['score']['total_score'] >= min_score]

if __name__ == "__main__":
    pass # for testing
