class TitlePrompt():
    prompt: str
    original_title: str
    twisted_title: str

    def __init__(self, prompt: str, original_title: str, twisted_title: str):
        self.prompt = prompt
        self.original_title = original_title
        self.twisted_title = twisted_title
    

title_prompts = {
    1: TitlePrompt(
        prompt="""A fiercely competitive nun-in-training joins a prestigious convent program where she strives to prove her faith and skill in leading the choir while clashing with the equally talented and stoic Sister Ice to defeat the russians.""",
        original_title="top gun",
        twisted_title="top nun",
    )
}
