"""
Resume Screening system - Main Module
Match resumes against JDs and rank by relevance
"""

import csv
import json
from pathlib import Path
from datetime import datetime
import argparse
import sys

from parsers import ResumeParser, JDParser
from extractors import KeywordExtractor
from matcher import ResumeScorer


class ResumeScreeningSystem:
    """Mainn application"""

    def __init__(
        self,
        config_path: str | Path | None = None,
        taxonomy_path: str | Path | None = None,
    ):
        """
        Initialize the screening system

        Args:
            config_path: Path to configuration file
            taxonomy_path: Path to skills taxonomy file
        """

        if config_path is None:
            config_path = Path(__file__).parent / "data" / "config.json"
        if taxonomy_path is None:
            taxonomy_path = Path(__file__).parent / "data" / "skills_taxonomy.json"

        self.resume_parser = ResumeParser()
        self.jd_parser = JDParser()
        self.extractor = KeywordExtractor(str(taxonomy_path))
        self.scorer = ResumeScorer(
            str(config_path) if Path(config_path).exists() else None
        )

        print("✔️  Resume Screening System initialized")

    def run(
        self,
        jd_path: str,
        resume_source: str,
        top_n: int = 10,
        min_score: float | None = None,
        output_format: str = "csv",
    ):
        """
        Run the complete screening process

        Args:
            jd_path: Path to job description file
            resume_source: Path to resume directory of JSONL file
            top_n : Number of top matches to return
            min_score: Minimum score threshold (0-100)
            output_format: Output format ('csv' or 'json')
        """
        print(f"\n{'='*60}")
        print("RESUME SCREENING SYSTEM")
        print(f"\n{'='*60}")

        # Step 1 : Parse JDs
        print("Step 1: Parsing Job Description...")
        try:
            jd_data = self.jd_parser.parse_file(jd_path)
            print(f"✔️  Required skills: {len(jd_data['required_skills'])}")
            print(f"✔️  Preferred skills: {len(jd_data['preferred_skills'])}")
            print(f"✔️  Min Experience: {jd_data['min_experience']} years")
        except Exception as e:
            print(f"❌  Error parsing job description: {e}")
            return

        # Step 2: Parse Resumes
        print(f"\nStep 2: Parsing Resumes from {resume_source}...")
        try:
            resumes = self._load_resumes(resume_source)
            print(f"✔️  Loaded {len(resumes)} resumes")
        except Exception as e:
            print(f"❌  Error loading resumes: {e}")
            return

        if not resumes:
            print("❌  No resumes found")
            return

        # Step 3: Extract & Score
        print(f"\nStep 3: Extracting skills and scoring resumes...")
        scored_resumes = []

        for idx, resume in enumerate(resumes, 1):
            if idx % 10 == 0:
                print(f"⏳  Processed {idx}/{len(resumes)} resumes...")

            resume_skills = self.extractor.extract_skills(resume["text"])
            resume_experience = self.extractor.extract_experience_years(resume["text"])
            resume_keywords = self.extractor.extract_keywords(resume["text"])

            score = self.scorer.score_resume(
                resume_skills, resume_experience, resume_keywords, jd_data
            )

            scored_resumes.append(
                {
                    "resume": resume,
                    "score": score,
                    "skills": list(resume_skills),
                    "experience": resume_experience,
                }
            )
        print(f"✔️  Scored {len(scored_resumes)} resumes")

        print(f"\nStep 4: Ranking and filtering results...")

        if min_score is not None:
            scored_resumes = [
                r for r in scored_resumes if r["score"]["total_score"] >= min_score
            ]
            print(
                f"✔️  Filtered to {len(scored_resumes)} resumes above {min_score}% threshold"
            )

        ranked_resumes = sorted(
            scored_resumes, key=lambda x: x["score"]["total_score"], reverse=True
        )

        top_resumes = ranked_resumes[:top_n]
        print(f"✔️  Selected top {len(top_resumes)} matches")

        print(f"\nStep 5: Generating output...")
        output_path = self._save_results(top_resumes, jd_path, output_format)
        print(f"✔️  Results saved to: {output_path}")

        self._display_summary(top_resumes, jd_data)

    def _load_resumes(self, source: str) -> list:
        """Load resumes from directory or JSONL file"""
        source_path = Path(source)

        if not source_path.exists():
            raise FileNotFoundError(f"Resume source not found: {source}")

        if source_path.is_file() and source_path.suffix == ".jsonl":
            return self.resume_parser.parse_jsonl(str(source_path))
        elif source_path.is_dir():
            return self.resume_parser.parse_directory(str(source_path))
        else:
            raise ValueError(f"Invalid resume source: {source}")

    def _save_results(self, results: list, jd_path: str, output_format: str) -> str:
        """Save results to output file"""
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        jd_name = Path(jd_path).stem

        if output_format == "csv":
            output_path = output_dir / f"results_{jd_name}_{timestamp}.csv"
            self._save_csv(results, output_path)
        else:
            output_path = output_dir / f"results_{jd_name}_{timestamp}.json"
            self._save_json(results, output_path)

        return str(output_path)

    def _save_csv(self, results: list, output_path: Path):
        """Save results to CSV file"""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(
                [
                    "Rank",
                    "Name",
                    "Email",
                    "Phone",
                    "Total Score (%)",
                    "Required Skills (%)",
                    "Preferred Skills (%)",
                    "Experience (%)",
                    "Keyword Match (%)",
                    "Experience (Years)",
                    "Matched Skills",
                    "Missing Skills",
                ]
            )

            for rank, result in enumerate(results, 1):
                resume = result["resume"]
                score = result["score"]

                writer.writerow(
                    [
                        rank,
                        resume.get("name", "Unknown"),
                        resume.get("email", ""),
                        resume.get("phone", ""),
                        score["total_score"],
                        score["required_skills_score"],
                        score["preferred_skills_score"],
                        score["experience_score"],
                        score["keyword_score"],
                        score["resume_experience"],
                        ", ".join(score["matched_required_skills"][:10]),
                        ", ".join(score["missing_required_skills"][:10]),
                    ]
                )

    def _save_json(self, results: list, output_path: Path):
        """Output results to a JSON file"""
        output_data = []

        for rank, result in enumerate(results, 1):
            resume = result["resume"]
            score = result["score"]

            output_data.append(
                {
                    "rank": rank,
                    "name": resume.get("name", "Unknown"),
                    "email": resume.get("email", ""),
                    "phone": resume.get("phone", ""),
                    "total_score": score["total_score"],
                    "scores": {
                        "required_skills": score["required_skills_score"],
                        "preferred_skills": score["preferred_skills_score"],
                        "experience": score["experience_score"],
                        "keyword_match": score["keyword_score"],
                    },
                    "experience_years": score["resume_experience"],
                    "matched_required_skills": score["matched_required_skills"],
                    "matched_preferred_skills": score["matched_preferred_skills"],
                    "missing_required_skills": score["missing_required_skills"],
                }
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f)

    def _display_summary(self, results: list, jd_data: dict):
        """Display summary of top results"""
        print(f"\n{'='*60}")
        print("TOP MATCHING RESUMES")
        print(f"\n{'='*60}\n")

        for rank, result in enumerate(results[:5], 1):
            resume = result["resume"]
            score = result["score"]

            print(f"#{rank} - {resume.get('name', 'Unknown')}")
            print(f"     Score: {score['total_score']:.1f}%")
            print(f"     Experience: {score['resume_experience']} years")
            print(
                f"     Matched Skills: {', '.join(score['matched_required_skills'][:5])}"
            )
            if score["missing_required_skills"]:
                print(
                    f"     Missing: {', '.join(score['missing_required_skills'][:3])}"
                )
            print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Resume Screening System - Matches resumes against job descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Screen resumes from JSONL file, get top 10
            python main.py --jd data/job_description.txt --resumes resumes_dataset.jsonl

            # Screen resumes from directory, get top 20
            python main.py --jd data/job_description.txt --resumes resumes/ --top 20

            # With minimum score threshold
            python main.py --jd data/job_description.txt --resumes resumes_dataset.jsonl --top 15 --min-score 60

            # Output as JSON
            python main.py --jd data/job_description.txt --resumes resumes_dataset.jsonl --format json
        """
    )

    parser.add_argument(
        '--jd', required=True, help="Path to job description file (TXT format)"
    )

    parser.add_argument(
        "--resumes", required=True, help="Path to resume directory or JSONL file"
    )

    parser.add_argument(
        "--top", type=int, default=10, help="Number of top matches to return (default: 10)"
    )

    parser.add_argument(
        "--min-score", type=float, default=None, help="Minimum score threshold 0-100 (default: no threshold)"
    )

    parser.add_argument(
        '--format', choices=['csv', 'json'], default='csv', help='Output format (default: csv)'
    )

    parser.add_argument(
        "--config", default=None, help="Path to custom config file (default: data/config.json)"
    )

    parser.add_argument(
        '--taxonomy', default=None, help="Path to custom skills taxonomy (default: data/skills_taxonomy.json)"
    )

    args = parser.parse_args()

    try:
        system = ResumeScreeningSystem(args.config, args.taxonomy)
    except Exception as e:
        print(f"Error initializing system: {e}")
        sys.exit(1)

    try:
        system.run(
            jd_path=args.jd,
            resume_source=args.resumes,
            top_n=args.top,
            min_score=args.min_score,
            output_format=args.format
        )
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during screening: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
