import os
import requests
import json

class DocumentRequestAgent:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY', '')
        self.use_ai = bool(self.api_key)

    def generate_request(self, candidate_data):
        if self.use_ai:
            try:
                return self._generate_with_ai(candidate_data)
            except Exception as e:
                return self._generate_fallback_message(candidate_data)
        else:
            return self._generate_fallback_message(candidate_data)

    def _generate_with_ai(self, candidate_data):
        prompt = f"""You are an AI assistant helping HR collect identity documents from candidates.

Candidate Information:
- Name: {candidate_data.get('name', 'Candidate')}
- Email: {candidate_data.get('email', 'N/A')}
- Phone: {candidate_data.get('phone', 'N/A')}
- Company: {candidate_data.get('company', 'N/A')}
- Designation: {candidate_data.get('designation', 'N/A')}

Task: Generate a professional, personalized message requesting PAN and Aadhaar documents from this candidate.

Requirements:
1. Be polite and professional
2. Personalize the message using the candidate's information
3. Clearly state what documents are needed (PAN and Aadhaar)
4. Explain why these documents are required (identity verification for employment process)
5. Provide clear instructions on how to submit
6. Keep it concise (3-4 paragraphs)

Generate the message:"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content'].strip()
            if message:
                return message
            else:
                raise ValueError("Empty response from AI")
        else:
            raise Exception(f"API error: {response.status_code}")

    def _generate_fallback_message(self, candidate_data):
        name = candidate_data.get('name', 'Candidate')
        greeting = f"Dear {name},"
        context = "Thank you for your application for Software Position at TraqCheck. We are pleased to inform you that we are moving forward with your candidacy."
        contact_hint = "You can reach us at the email address we have on file (hr@traqcheck.com) if you have any questions."

        message = f"""{greeting}

{context}

As part of our standard verification process, we require you to submit the following identity documents:

1. PAN Card (Permanent Account Number) - A clear, legible copy of your PAN card
2. Aadhaar Card - A clear, legible copy of your Aadhaar card

These documents are essential for:
- Identity verification
- Compliance with employment regulations
- Background verification process
- Joining formalities

Please upload both documents through our secure candidate portal at your earliest convenience. Ensure that:
- All text is clearly visible
- The documents are in color (if original is in color)
- File formats are PDF, JPG, or PNG
- File sizes are under 5MB each

{contact_hint}

We look forward to receiving your documents and proceeding with the next steps of your application.

Best regards,
HR Team"""

        return message
