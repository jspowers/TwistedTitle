from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def get_twisted_title_description( 
    original_movie: str = "",
    modified_movie: str = "",
    plot_suggestion: str = "",
    endpoint_url="https://api.openai.com/v1/chat/completions"
    ):
    
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[

        {
      "role": "developer",
      "content": [
        {
          "type": "text",
          "text": """You generate concise, detail-rich plot rewrites of movie concepts based on modified titles. Users will provide an original movie title, a modified title, and a suggested plot change. The GPT will craft a brief plot summary closely aligned with the original movie's story, adjusted to fit both the modified title's new context and the suggested plot change. The focus will always be on the storyline, incorporating enough specific details from the original movie to serve as good clues for someone guessing the title. The output is limited to a maximum of two sentences or 50 words, whichever is shorter, and it avoids using any of the same words from the provided 'Original Movie' or 'Modified Movie' titles. The style is straightforward, with minimal use of adjectives, and avoids naming the original title or directly comparing it to the modified version. The resulting plot summary should feel natural and plausible while maintaining the essence of the original story while integrating the suggested plot change."""
        }
      ]
    },
        {
            "role": "user", 
            "content": [
                {
                "type": "text",
                "text": f"""Original Movie: {original_movie}; Modified Movie: {modified_movie}; Plot Suggestion: {plot_suggestion}"""
                }
                ],
        },
    ]
    )

    return completion.choices[0].message.content


# Example usage
if __name__ == "__main__":
    question = "What is the capital of France?"
    response = get_twisted_title_description()
    print("GPT Response:", response)