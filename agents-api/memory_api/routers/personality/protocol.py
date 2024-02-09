from pydantic import BaseModel, field_validator, Field


class Answer(BaseModel):
    question_number: int = Field(..., alias="questionNumber")
    answer_number: int = Field(..., alias="answerNumber")

    @field_validator("answer_number")
    @classmethod
    def check_answer(cls, answer_number: int) -> int:
        if 1 <= answer_number <= 7:
            return answer_number
        raise ValueError("answer value must be between 1 and 7")


class AnswersRequest(BaseModel):
    answers: list[Answer]
