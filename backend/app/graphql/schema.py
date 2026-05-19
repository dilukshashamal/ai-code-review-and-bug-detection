import strawberry

from app.graphql.types import CodeReview, DashboardStats
from app.graphql.inputs import CodeInput
from app.services.review_service import review_service


@strawberry.type
class Query:
    @strawberry.field
    async def review_history(self) -> list[CodeReview]:
        return review_service.list_reviews()

    @strawberry.field
    async def review_report(self, id: strawberry.ID) -> CodeReview | None:
        return review_service.get_review(str(id))

    @strawberry.field
    async def dashboard_stats(self) -> DashboardStats:
        return review_service.get_dashboard_stats()


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def analyze_code(self, input: CodeInput) -> CodeReview:
        return review_service.analyze_code(input)


schema = strawberry.Schema(query=Query, mutation=Mutation)
