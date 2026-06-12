"""
Keyword Extractor Module
Extracts contact info, skills, and technical keywords from resume text
"""

import re
import json
from datetime import date
from pathlib import Path


class KeywordExtractor:
    """Extracts contact info, skills, and technical keywords from resume text"""

    def __init__(self, skills_taxonomy_path: str | None = None):
        """
        Initialize extractor with optional skills taxonomy

        Args:
            skills_taxonomy_path: Path to skills taxonomy JSON file
        """
        self.skills_taxonomy = self._load_skills_taxonomy(skills_taxonomy_path)

    def _load_skills_taxonomy(self, skills_taxonomy_path: str | None = None) -> dict:
        """Load skills taxonomy from JSON file"""
        if skills_taxonomy_path and Path(skills_taxonomy_path).exists():
            try:
                with open(skills_taxonomy_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading skills taxonomy: {e}")

        # return default file
        return self._get_default_taxonomy()

    def _get_default_taxonomy(self) -> dict:
        """Get default skills taxonomy with synonyms"""
        return {
            "programming_languages": {
                "java": ["java", "j2ee", "jdk", "jre", "java 8", "java 11", "java 17"],
                "python": ["python", "python3", "py"],
                "javascript": [
                    "javascript",
                    "js",
                    "jsx",
                    "ecmascript",
                    "es6",
                    "es2015",
                ],
                "typescript": ["typescript", "ts", "tsx"],
                "csharp": ["c#", "csharp", ".net", "dotnet", "chash"],
                "cpp": ["c++", "cpp"],
                "go": ["go", "golang"],
                "rust": ["rust"],
                "ruby": ["ruby", "rails"],
                "php": ["php"],
                "kotlin": ["kotlin"],
                "scala": ["scala"],
                "swift": ["swift"],
            },
            "frameworks": {
                "spring": [
                    "spring",
                    "spring boot",
                    "spring mvc",
                    "spring framework",
                    "spring cloud",
                ],
                "hibernate": ["hibernate", "jpa"],
                "django": ["django"],
                "flask": ["flask"],
                "fastapi": ["fastapi"],
                "react": ["react", "reactjs", "react.js"],
                "angular": ["angular", "angularjs", "angular.js"],
                "vue": ["vue", "vuejs", "vue.js"],
                "nodejs": ["node", "nodejs", "node.js"],
                "express": ["express", "expressjs", "express.js"],
                "aspnet": ["aspnet", "asp.net"],
                "struts": ["struts"],
                "jsf": ["jsf", "java server faces"],
            },
            "databases": {
                "mysql": ["mysql"],
                "postgresql": ["postgres", "postgresql"],
                "mongodb": ["mongodb", "mongo"],
                "oracle": ["oracle", "oracle db", "oracle database"],
                "sqlserver": ["sql server", "mssql", "ms sql"],
                "redis": ["redis"],
                "cassandra": ["cassandra"],
                "dynamodb": ["dynamo", "dynamodb"],
                "db2": ["db2"],
            },
            "cloud": {
                "aws": [
                    "aws",
                    "amazon web services",
                    "ec2",
                    "s3",
                    "lambda",
                    "cloudformation",
                ],
                "azure": ["azure", "microsoft azure"],
                "gcp": ["gcp", "google cloud", "google cloud platform"],
            },
            "devops": {
                "docker": ["docker"],
                "kubernetes": ["kubernetes", "k8s"],
                "jenkins": ["jenkins"],
                "git": ["git", "github", "gitlab", "bitbucket"],
                "cicd": [
                    "ci/cd",
                    "cicd",
                    "continuous integration",
                    "continuous deployment",
                ],
                "maven": ["maven"],
                "gradle": ["gradle"],
                "ansible": ["ansible"],
                "terraform": ["terraform"],
            },
            "web_technologies": {
                "html": ["html", "html5"],
                "css": ["css", "css3", "sass", "less"],
                "rest": ["rest" "restful", "rest api"],
                "soap": ["soap"],
                "microservices": ["microservices", "microservice"],
                "graphql": ["graphql"],
                "json": ["json"],
                "xml": ["xml"],
            },
            "methodologies": {
                "agile": ["agile"],
                "scrum": ["scrum"],
                "kanban": ["kanban"],
                "devops": ["devops"],
                "tdd": ["tdd", "test driven development"],
                "bdd": ["bdd", "behaviour driven development"],
            },
        }

    def extract_skills(self, text: str) -> set[str]:
        """
        Extract technical skills from resume text

        Args:
            text: Resume text

        Returns:
            set of normalized skill names
        """
        text_lower = text.lower()
        found_skills = set()

        for category, skills_dict in self.skills_taxonomy.items():
            for skill_name, variations in skills_dict.items():
                for variation in variations:
                    pattern = r"\b" + re.escape(variation) + r"\b"
                    if re.search(pattern, text_lower):
                        found_skills.add(skill_name)
                        break

        return found_skills

    def _extract_contact_info(self, text: str) -> dict[str, str]:
        """
        Extract contact information from resume text

        Args:
            text: Resume text

        Returns:
            Dictionary with email, phone, and name
        """
        return {
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "name": self._extract_name(text),
        }

    def _extract_email(self, text: str) -> str:
        """Extract Email address"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        matches = re.findall(email_pattern, text)

        # filter out generic/placeholder emails
        for email in matches:
            email_lower = email.lower()
            if "example" not in email_lower and "sample" not in email_lower:
                return email

        return matches[0] if matches else ""

    def _extract_phone(self, text: str) -> str:
        """ "Extract phone number"""
        # possible patterns
        phone_patterns = [
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # 123-456-7890
            r"\b(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b",  # (123) 456-7890
            r"\b\d{10}\b",  # 1234567890
            r"\+\d{1,3}[-.\s]?d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # +1-123-456-7890
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # validate its not a pincode or other number
                if len(re.sub(r"\D", "", phone)) >= 10:
                    return phone

        return ""

    def _extract_name(self, text: str) -> str:
        """Extract name, this is usually present at the beginning of the resume"""
        # looking for name in first 5 lines
        lines = text.split("\n")[:5]

        # Name pattern: 2-4 capitalized words
        name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"

        for line in lines:
            # skip lines with email or phone
            if "@" in line or re.search(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}", line):
                continue

            match = re.search(name_pattern, line)
            if match:
                name = match.group(1).strip()
                # filter out common headings that may get detected
                if name.lower() not in ["resume", "curriculum vitae", "summary"]:
                    return name

        return ""

    def extract_experience_years(self, text: str) -> int:
        """
        Extract years of experience from resume

        Args:
            text: resume text

        Returns:
            Number of years of experience
        """
        text_lower = text.lower()
        years = []

        # Pattern: "X years of experience"
        patterns = [
            r"(\d+)\+?\s*(?:years?|yrs?).*?(?:experience|exp)",
            r'("?:experience|exp).*?(\d+)\+?\s*(?:years?|yrs?)'
            r"over\s+(\d+)\s+(?:years?|yrs?)",
            r"more\s+than\s+(\d+)\s+(?:years?|yrs?)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    year = int(match.group(1))
                    if 0 < year < 50:  # sanity check
                        years.append(year)
                except (ValueError, IndexError):
                    continue

        # trying to extract from date ranges given in work from and till
        date_years = self._calculate_experience_from_dates(text)
        if date_years:
            years.append(date_years)

        return max(years) if years else 0

    def _calculate_experience_from_dates(self, text: str) -> int:
        """Calculate total years of experience from employment date ranges"""
        # Pattern: MM/YYYY - MM/YYYY or YYYY-YYYY
        date_patterns = [
            r"(\d{4})\s*[--]\s*(\d{1,2}/\d{4}|present|current)",
            r"(\d{1,2}/\d{4})\s*[--]\s*(\d{1,2}/\d{4}|present|current)",
        ]

        total_years = 0

        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = match.group(1)
                end = match.group(2)

                try:
                    # Extract year from start date
                    start_year = int(re.search(r"\d{4}", start).group())

                    # Extract year from end date or use current year
                    if end.lower() in ["present", "current"]:
                        end_year = date.today().year  # current year
                    else:
                        end_year = int(re.search(r"\d{4}", end).group())

                    # calculate years (min 0)
                    years = max(0, end_year - start_year)
                    if years > 0 and years < 30:  # sanity check
                        total_years += years

                except (ValueError, AttributeError):
                    continue
        return total_years

    def extract_keywords(self, text: str) -> list[str]:
        """
        Extract all important keywords for matching

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords (may include duplicates)
        """

        text_lower = text.lower()
        keywords = []

        for category, skills_dict in self.skills_taxonomy.items():
            for skill_name, variations in skills_dict.items():
                for variation in variations:
                    pattern = r"\b" + re.escape(variation) + r"\b"
                    matches = re.findall(pattern, text_lower)
                    keywords.extend(matches)

        return keywords

    def calculate_keyword_density(self, text: str, keywords: list[str]) -> float:
        """
        Calculate keyword density (keyword freq. relative to text length)

        Args:
            text: text to analyze
            keywords: list of keywords to search for

        Returns:
            Keyword density score (0-1)
        """
        if not text or not keywords:
            return 0.0

        text_lower = text.lower()
        total_words = len(text_lower.split())

        keyword_count = 0
        for keyword in keywords:
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            matches = re.findall(pattern, text_lower)
            keyword_count += len(matches)

        # normalize by text length
        density = min(1.0, keyword_count / total_words * 10)
        return density

if __name__ == "__main__":
    # write according to test case
    extractor = KeywordExtractor()
    pass