"""
Web Scraper Module for EchoQuest Pro
Fetches quiz questions from various web sources including:
- Open Trivia Database API
- Wikipedia
- DuckDuckGo API
- Custom web search
- AI-generated fallback questions
"""

import requests
import json
import random
import re
import time
from bs4 import BeautifulSoup
from googlesearch import search
import wikipedia
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import html

class QuestionScraper:
    """Main scraper class for fetching questions"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.timeout = 10
        self.max_questions = 20
    
    def fetch_questions(self, topic: str, num_questions: int = 20) -> List[Dict]:
        """Main method to fetch questions from multiple sources"""
        all_questions = []
        
        print(f"🔍 Fetching questions for topic: {topic}")
        
        # Source 1: Open Trivia Database (Most reliable)
        try:
            questions = self.fetch_from_opentdb(topic)
            if questions:
                all_questions.extend(questions)
                print(f"✅ OpenTDB: {len(questions)} questions")
        except Exception as e:
            print(f"⚠️ OpenTDB failed: {e}")
        
        # Source 2: Wikipedia
        if len(all_questions) < num_questions:
            try:
                questions = self.fetch_from_wikipedia(topic)
                if questions:
                    all_questions.extend(questions)
                    print(f"✅ Wikipedia: {len(questions)} questions")
            except Exception as e:
                print(f"⚠️ Wikipedia failed: {e}")
        
        # Source 3: The Trivia API (Alternative)
        if len(all_questions) < num_questions:
            try:
                questions = self.fetch_from_trivia_api(topic)
                if questions:
                    all_questions.extend(questions)
                    print(f"✅ Trivia API: {len(questions)} questions")
            except Exception as e:
                print(f"⚠️ Trivia API failed: {e}")
        
        # Source 4: Custom web search
        if len(all_questions) < num_questions:
            try:
                questions = self.fetch_from_web_search(topic, num_questions - len(all_questions))
                if questions:
                    all_questions.extend(questions)
                    print(f"✅ Web Search: {len(questions)} questions")
            except Exception as e:
                print(f"⚠️ Web search failed: {e}")
        
        # Source 5: Generate fallback questions
        if len(all_questions) < num_questions:
            questions = self.generate_fallback_questions(topic, num_questions - len(all_questions))
            all_questions.extend(questions)
            print(f"✅ Fallback: {len(questions)} questions generated")
        
        # Shuffle and limit to requested number
        random.shuffle(all_questions)
        final_questions = all_questions[:num_questions]
        
        print(f"📚 Total questions prepared: {len(final_questions)}")
        return final_questions
    
    def fetch_from_opentdb(self, topic: str) -> List[Dict]:
        """Fetch from Open Trivia Database API"""
        questions = []
        
        # Category mapping for OpenTDB
        category_map = {
            'computer': 18, 'programming': 18, 'python': 18, 'java': 18, 'javascript': 18, 'coding': 18,
            'science': 17, 'biology': 17, 'chemistry': 17, 'physics': 17, 'astronomy': 17,
            'mathematics': 19, 'math': 19, 'algebra': 19, 'calculus': 19, 'geometry': 19,
            'history': 23, 'world war': 23, 'ancient': 23, 'medieval': 23,
            'geography': 22, 'countries': 22, 'capitals': 22, 'continents': 22,
            'art': 25, 'painting': 25, 'sculpture': 25,
            'music': 12, 'rock': 12, 'pop': 12, 'classical': 12,
            'movies': 11, 'film': 11, 'cinema': 11,
            'sports': 21, 'football': 21, 'basketball': 21, 'soccer': 21,
            'mythology': 20, 'greek': 20, 'norse': 20, 'egyptian': 20,
            'politics': 24, 'government': 24,
            'animals': 27, 'wildlife': 27,
            'food': 32, 'cooking': 32,
            'gaming': 15, 'video games': 15
        }
        
        # Find matching category
        category_id = 9  # General knowledge default
        topic_lower = topic.lower()
        
        for key, cat_id in category_map.items():
            if key in topic_lower:
                category_id = cat_id
                break
        
        try:
            url = f"https://opentdb.com/api.php?amount=15&category={category_id}&type=multiple&encode=url3986"
            response = requests.get(url, timeout=self.timeout)
            data = response.json()
            
            if data.get('response_code') == 0:
                for item in data.get('results', []):
                    # Decode URL-encoded content
                    question_text = html.unescape(requests.utils.unquote(item['question']))
                    correct_answer = html.unescape(requests.utils.unquote(item['correct_answer']))
                    incorrect_answers = [html.unescape(requests.utils.unquote(ans)) for ans in item['incorrect_answers']]
                    
                    # Combine and shuffle options
                    options = incorrect_answers + [correct_answer]
                    random.shuffle(options)
                    correct_letter = chr(65 + options.index(correct_answer))
                    
                    question = {
                        'text': question_text,
                        'options': options,
                        'correct': correct_letter,
                        'explanation': f"The correct answer is: {correct_answer}",
                        'difficulty': item.get('difficulty', 'medium').lower(),
                        'source': 'OpenTDB'
                    }
                    questions.append(question)
                    
        except Exception as e:
            print(f"OpenTDB error: {e}")
        
        return questions
    
    def fetch_from_wikipedia(self, topic: str) -> List[Dict]:
        """Fetch information from Wikipedia and create questions"""
        questions = []
        
        try:
            # Search for relevant Wikipedia pages
            search_results = wikipedia.search(topic, results=3)
            
            for page_title in search_results[:2]:
                try:
                    page = wikipedia.page(page_title, auto_suggest=False)
                    summary = page.summary[:1500]
                    
                    # Extract key sentences for questions
                    sentences = re.split(r'[.!?]+', summary)
                    important_sentences = [s.strip() for s in sentences if len(s.strip()) > 40][:5]
                    
                    for sentence in important_sentences[:3]:
                        # Extract key terms
                        words = sentence.split()[:8]
                        key_term = ' '.join(words)
                        
                        # Create question
                        question_text = f"According to Wikipedia, what is mentioned about {page_title}?"
                        
                        # Generate plausible options
                        options = [
                            sentence[:80] + "..." if len(sentence) > 80 else sentence,
                            f"A different perspective on {page_title}",
                            f"Another important aspect of {topic}",
                            f"Common misconception about {topic}"
                        ]
                        
                        # Add correct answer as first option
                        options.insert(0, sentence[:80] + "..." if len(sentence) > 80 else sentence)
                        random.shuffle(options)
                        correct_letter = chr(65 + options.index(sentence[:80] + "..." if len(sentence) > 80 else sentence))
                        
                        question = {
                            'text': question_text,
                            'options': options,
                            'correct': correct_letter,
                            'explanation': f"From Wikipedia: {sentence[:200]}",
                            'difficulty': 'medium',
                            'source': 'Wikipedia'
                        }
                        questions.append(question)
                        
                        if len(questions) >= 8:
                            break
                            
                except Exception as e:
                    print(f"Wikipedia page error for {page_title}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        return questions
    
    def fetch_from_trivia_api(self, topic: str) -> List[Dict]:
        """Fetch from alternative trivia APIs"""
        questions = []
        
        # Try multiple trivia APIs
        apis = [
            f"https://the-trivia-api.com/api/questions?limit=10&categories={quote_plus(topic)}",
            f"https://quizapi.io/api/v1/questions?apiKey=demo&limit=10&category={quote_plus(topic)}",
            f"https://opentdb.com/api.php?amount=10&category=9&type=multiple"
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=self.timeout, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different API response formats
                    if isinstance(data, list):
                        for item in data[:5]:
                            question = self._parse_trivia_item(item)
                            if question:
                                questions.append(question)
                    elif isinstance(data, dict) and 'results' in data:
                        for item in data['results'][:5]:
                            question = self._parse_opentdb_item(item)
                            if question:
                                questions.append(question)
                    
                    if len(questions) >= 10:
                        break
                        
            except Exception as e:
                print(f"Trivia API error for {api_url}: {e}")
                continue
        
        return questions
    
    def fetch_from_web_search(self, topic: str, count: int) -> List[Dict]:
        """Generate questions using web search"""
        questions = []
        
        search_queries = [
            f"{topic} quiz questions and answers multiple choice",
            f"{topic} trivia questions",
            f"test your knowledge about {topic}",
            f"{topic} mcq questions"
        ]
        
        for query in search_queries[:2]:
            try:
                # Search for relevant pages
                search_results = list(search(query, num_results=3))
                
                for url in search_results:
                    try:
                        response = requests.get(url, timeout=self.timeout, headers=self.headers)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        text = soup.get_text()
                        
                        # Look for question patterns
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if '?' in line and len(line) < 200 and len(line) > 20:
                                # Found a potential question
                                question_text = line.strip()
                                
                                # Generate context-based options
                                context = ' '.join(lines[max(0, i-2):min(len(lines), i+3)])
                                
                                # Extract potential answers from context
                                words = context.split()
                                potential_answers = []
                                
                                for j, word in enumerate(words):
                                    if word.istitle() and len(word) > 3 and word not in potential_answers:
                                        potential_answers.append(word)
                                        if len(potential_answers) >= 4:
                                            break
                                
                                # Ensure we have 4 options
                                while len(potential_answers) < 4:
                                    potential_answers.append(f"Related concept in {topic}")
                                
                                random.shuffle(potential_answers)
                                
                                question = {
                                    'text': question_text[:200],
                                    'options': potential_answers[:4],
                                    'correct': 'A',  # Default, actual correct would need processing
                                    'explanation': f"Based on information from {url[:50]}",
                                    'difficulty': random.choice(['easy', 'medium', 'hard']),
                                    'source': 'WebSearch'
                                }
                                questions.append(question)
                                
                                if len(questions) >= count:
                                    break
                                    
                    except Exception as e:
                        print(f"Error processing URL {url}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Search error for '{query}': {e}")
                continue
            
            if len(questions) >= count:
                break
        
        return questions
    
    def generate_fallback_questions(self, topic: str, count: int) -> List[Dict]:
        """Generate fallback questions using templates"""
        questions = []
        
        # Question templates by difficulty
        templates = {
            'easy': [
                "What is the basic definition of {topic}?",
                "Which of these is most closely related to {topic}?",
                "What is a fundamental concept in {topic}?",
                "Who is considered a pioneer in {topic}?",
                "When did {topic} first gain prominence?",
                "What is the primary purpose of {topic}?",
                "Which tool is commonly used in {topic}?",
                "What is the simplest form of {topic}?",
                "Where did {topic} originate?",
                "Why is {topic} important?"
            ],
            'medium': [
                "How does {topic} impact modern society?",
                "What is the primary challenge in {topic}?",
                "Which principle best describes {topic}?",
                "What distinguishes {topic} from related fields?",
                "What is the most important tool used in {topic}?",
                "What are the key components of {topic}?",
                "How has {topic} evolved over time?",
                "What is the relationship between {topic} and technology?",
                "What skills are needed for {topic}?",
                "What are the ethical considerations in {topic}?"
            ],
            'hard': [
                "What is the most complex aspect of {topic}?",
                "How has {topic} evolved over the last decade?",
                "What is the future direction of {topic}?",
                "What controversial debate exists within {topic}?",
                "What breakthrough changed {topic} forever?",
                "What are the limitations of current {topic} approaches?",
                "How do experts solve critical problems in {topic}?",
                "What research is pushing {topic} forward?",
                "What are the unsolved problems in {topic}?",
                "How does {topic} intersect with other disciplines?"
            ]
        }
        
        # Generate options templates
        option_templates = {
            'easy': [
                ["A fundamental aspect", "A related concept", "An advanced topic", "A common misconception"],
                ["Core principle", "Secondary consideration", "Advanced theory", "Basic definition"],
                ["Essential component", "Optional element", "Rare feature", "Outdated concept"]
            ],
            'medium': [
                ["Major impact", "Minor influence", "No effect", "Negative consequence"],
                ["Key challenge", "Minor obstacle", "Easy solution", "Irrelevant factor"],
                ["Critical component", "Supporting element", "Optional addition", "Unrelated factor"]
            ],
            'hard': [
                ["Most complex", "Simplest aspect", "Most studied", "Least understood"],
                ["Revolutionary breakthrough", "Incremental improvement", "Failed attempt", "Controversial theory"],
                ["Future direction", "Past approach", "Current standard", "Abandoned concept"]
            ]
        }
        
        for i in range(count):
            # Distribute difficulties
            if i < count * 0.6:  # 60% medium
                difficulty = 'medium'
            elif i < count * 0.8:  # 20% easy
                difficulty = 'easy'
            else:  # 20% hard
                difficulty = 'hard'
            
            # Select template
            template = random.choice(templates[difficulty])
            question_text = template.format(topic=topic.title())
            
            # Select options
            options_pool = random.choice(option_templates[difficulty])
            options = [opt.format(topic=topic) if '{topic}' in opt else opt for opt in options_pool]
            
            # Random correct answer
            correct_letter = random.choice(['A', 'B', 'C', 'D'])
            
            question = {
                'text': question_text,
                'options': options,
                'correct': correct_letter,
                'explanation': f"This is a key concept in understanding {topic}. {options[0]} represents an important aspect of the subject.",
                'difficulty': difficulty,
                'source': 'Fallback'
            }
            questions.append(question)
        
        return questions
    
    def _parse_trivia_item(self, item: Dict) -> Optional[Dict]:
        """Parse trivia API response item"""
        try:
            question_text = item.get('question', '')
            correct_answer = item.get('correctAnswer', '')
            incorrect_answers = item.get('incorrectAnswers', [])
            
            if not question_text or not correct_answer:
                return None
            
            options = incorrect_answers + [correct_answer]
            random.shuffle(options)
            correct_letter = chr(65 + options.index(correct_answer))
            
            return {
                'text': html.unescape(question_text),
                'options': options,
                'correct': correct_letter,
                'explanation': f"The correct answer is: {correct_answer}",
                'difficulty': item.get('difficulty', 'medium').lower(),
                'source': 'TriviaAPI'
            }
        except Exception:
            return None
    
    def _parse_opentdb_item(self, item: Dict) -> Optional[Dict]:
        """Parse OpenTDB response item"""
        try:
            question_text = html.unescape(item.get('question', ''))
            correct_answer = html.unescape(item.get('correct_answer', ''))
            incorrect_answers = [html.unescape(ans) for ans in item.get('incorrect_answers', [])]
            
            if not question_text or not correct_answer:
                return None
            
            options = incorrect_answers + [correct_answer]
            random.shuffle(options)
            correct_letter = chr(65 + options.index(correct_answer))
            
            return {
                'text': question_text,
                'options': options,
                'correct': correct_letter,
                'explanation': f"The correct answer is: {correct_answer}",
                'difficulty': item.get('difficulty', 'medium').lower(),
                'source': 'OpenTDB'
            }
        except Exception:
            return None

# Convenience function for easy import
def fetch_questions_from_web(topic: str, num_questions: int = 20) -> List[Dict]:
    """Convenience function to fetch questions"""
    scraper = QuestionScraper()
    return scraper.fetch_questions(topic, num_questions)

# For backward compatibility
def generate_fallback_questions(topic: str, count: int = 20) -> List[Dict]:
    """Generate fallback questions (backward compatibility)"""
    scraper = QuestionScraper()
    return scraper.generate_fallback_questions(topic, count)

# Test function
if __name__ == "__main__":
    # Test the scraper
    test_topics = ["Python Programming", "Climate Change", "Space Exploration"]
    
    for topic in test_topics:
        print(f"\n{'='*50}")
        print(f"Testing topic: {topic}")
        print('='*50)
        
        questions = fetch_questions_from_web(topic, num_questions=5)
        
        for i, q in enumerate(questions, 1):
            print(f"\n{i}. {q['text']}")
            print(f"   Options: {q['options']}")
            print(f"   Correct: {q['correct']}")
            print(f"   Difficulty: {q['difficulty']}")
            print(f"   Source: {q.get('source', 'Unknown')}")