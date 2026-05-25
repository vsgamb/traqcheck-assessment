import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_MODEL = 'openrouter/free'
FALLBACK_MODELS = (
    'openrouter/free',
    'google/gemma-2-9b-it:free',
    'meta-llama/llama-3.2-3b-instruct:free',
    'qwen/qwen-2.5-7b-instruct:free',
)


class DocumentRequestAgent:
    def __init__(self):
        self.api_key = (os.getenv('OPENROUTER_API_KEY') or '').strip()
        self.model = (os.getenv('OPENROUTER_MODEL') or DEFAULT_MODEL).strip()
        self.referer = (os.getenv('OPENROUTER_REFERER') or 'http://localhost:5002').strip()
        self.app_name = (os.getenv('OPENROUTER_APP_NAME') or 'TraqCheck').strip()
        self.max_tokens = int(os.getenv('OPENROUTER_MAX_TOKENS', '1200'))
        self.min_message_chars = int(os.getenv('OPENROUTER_MIN_MESSAGE_CHARS', '350'))
        self.rate_limit_retries = int(os.getenv('OPENROUTER_RATE_LIMIT_RETRIES', '5'))
        self.rate_limit_wait = float(os.getenv('OPENROUTER_RATE_LIMIT_WAIT_SECONDS', '3'))
        self.hiring_company = (os.getenv('HIRING_COMPANY') or 'TraqCheck').strip()
        self.hiring_position = (os.getenv('HIRING_POSITION') or 'Software Engineer').strip()

    def generate_request(self, candidate_data):
        if not self._has_valid_api_key():
            message = self._fallback_message(candidate_data)
            return self._finalize_message(message) or message

        try:
            message, _ = self._generate_with_ai(candidate_data)
            message = self._finalize_message(message)
        except (requests.RequestException, RuntimeError, ValueError):
            message = self._finalize_message(self._fallback_message(candidate_data))

        if not message.strip():
            message = self._fallback_message(candidate_data)
        return message

    def _has_valid_api_key(self):
        if not self.api_key:
            return False
        placeholders = {'your_openrouter_api_key_here', 'sk-your-key-here', 'changeme'}
        return self.api_key.lower() not in placeholders

    def _job_context(self):
        return f'{self.hiring_position} Position at {self.hiring_company}'

    def _finalize_message(self, message):
        message = (message or '').strip()
        if not message:
            return message

        phrase = self._job_context()
        if phrase.lower() in message.lower():
            return message

        lines = [line for line in message.split('\n') if line.strip()]
        if not lines:
            return message

        intro = (
            f'Thank you for your application for the {phrase}. '
            'We are pleased to inform you that we are moving forward with your candidacy.'
        )
        greeting = lines[0]
        body = '\n'.join(lines[1:]).strip()
        return f'{greeting}\n\n{intro}\n\n{body}' if body else f'{greeting}\n\n{intro}'

    def _models_to_try(self):
        seen = set()
        models = []
        for model in [self.model, *FALLBACK_MODELS]:
            if model not in seen:
                seen.add(model)
                models.append(model)
        return models

    def _generate_with_ai(self, candidate_data):
        prompt = self._build_prompt(candidate_data)
        errors = []

        for index, model in enumerate(self._models_to_try()):
            if index > 0:
                time.sleep(1)

            try:
                message, finish_reason = self._call_openrouter(model, prompt)
                if not self._is_complete(message, finish_reason):
                    message = self._complete_message(model, message)
                message = self._finalize_message(message)
                if self._is_complete(message, 'stop'):
                    return message, model
                raise ValueError('Incomplete response')
            except RuntimeError as exc:
                error = str(exc)
                errors.append(error)
                if '404' in error or '429' in error:
                    continue
                raise
            except ValueError:
                continue

        raise RuntimeError('Unable to generate message with configured models')

    def _build_prompt(self, candidate_data):
        name = candidate_data.get('name', 'Candidate')
        email = candidate_data.get('email', 'N/A')
        phone = candidate_data.get('phone', 'N/A')
        role = self._job_context()

        return f"""Write a professional HR email requesting identity documents from a candidate.

Candidate:
- Name: {name}
- Email: {email}
- Phone: {phone}

Role: {role}

Requirements:
- Email body only, no subject line
- Greet the candidate by name
- Refer to the role as "{role}" only
- Request PAN and Aadhaar cards for identity verification
- Ask for uploads in PDF, JPG, or PNG via the candidate portal
- Close with "Best regards," and "HR Team"
- Write 3 complete paragraphs"""

    def _standard_closing(self):
        return """Please upload clear copies of your PAN and Aadhaar cards in PDF, JPG, or PNG format through the candidate portal.

Best regards,
HR Team"""

    def _complete_message(self, model, partial_message):
        continuation = ''
        prompt = f"""Continue this HR email from where it stopped. Do not repeat the opening.
Finish with "Best regards," and "HR Team".

{partial_message}

Continue:"""

        try:
            continuation, _ = self._call_openrouter(model, prompt)
        except (RuntimeError, ValueError):
            pass

        if continuation:
            return f'{partial_message.rstrip()}\n\n{continuation.lstrip()}'.strip()
        return f'{partial_message.rstrip()}\n\n{self._standard_closing()}'.strip()

    def _is_complete(self, message, finish_reason):
        text = message.strip()
        lower = text.lower()
        role = self._job_context().lower()

        if finish_reason == 'length':
            return False
        if len(text) < self.min_message_chars:
            return False
        if 'pan' not in lower or 'aadhaar' not in lower:
            return False
        if role not in lower:
            return False
        if text[-1] not in '.!?' and 'hr team' not in lower:
            return False
        return True

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': self.referer,
            'X-OpenRouter-Title': self.app_name,
        }

    def _parse_retry_wait(self, response):
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return max(float(retry_after), 1.0)
            except ValueError:
                pass

        try:
            metadata = response.json().get('error', {}).get('metadata', {})
            seconds = metadata.get('retry_after_seconds') or metadata.get('retry_after_seconds_raw')
            if seconds is not None:
                return max(float(seconds), 1.0)
        except (ValueError, TypeError, AttributeError):
            pass

        return self.rate_limit_wait

    def _call_openrouter(self, model, prompt):
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You write complete professional HR emails with a proper sign-off.',
                },
                {'role': 'user', 'content': prompt},
            ],
            'max_tokens': self.max_tokens,
            'temperature': 0.5,
        }

        last_error = None
        for attempt in range(1, self.rate_limit_retries + 1):
            response = requests.post(
                OPENROUTER_URL,
                headers=self._headers(),
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                choice = response.json()['choices'][0]
                content = (choice.get('message') or {}).get('content')
                message = (content or '').strip()
                if not message:
                    raise ValueError('Empty model response')
                return message, choice.get('finish_reason')

            if response.status_code == 429 and attempt < self.rate_limit_retries:
                time.sleep(self._parse_retry_wait(response))
                last_error = RuntimeError(f'OpenRouter API error 429: {response.text[:300]}')
                continue

            raise RuntimeError(
                f'OpenRouter API error {response.status_code}: {response.text[:500]}'
            )

        if last_error:
            raise last_error
        raise RuntimeError(f'OpenRouter request failed for model={model}')

    def _fallback_message(self, candidate_data):
        name = candidate_data.get('name', 'Candidate')
        role = self._job_context()

        return f"""Dear {name},

Thank you for your application for the {role}. We are pleased to inform you that we are moving forward with your candidacy.

As part of our standard verification process, we require you to submit the following identity documents:

1. PAN Card (Permanent Account Number) - A clear, legible copy of your PAN card
2. Aadhaar Card - A clear, legible copy of your Aadhaar card

These documents are essential for identity verification, compliance with employment regulations, background verification, and joining formalities.

Please upload both documents through our secure candidate portal at your earliest convenience. Accepted formats are PDF, JPG, or PNG (max 5MB each). Ensure all details are clearly visible.

If you have any questions, please contact us at hr@traqcheck.com.

We look forward to receiving your documents and proceeding with the next steps of your application.

Best regards,
HR Team"""
