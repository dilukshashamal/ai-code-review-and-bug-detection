import strawberry


@strawberry.input
class CodeInput:
    language: str
    code: str
    title: str | None = None
    context: str | None = None
