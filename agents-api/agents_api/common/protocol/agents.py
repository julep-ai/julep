from pydantic import BaseModel


class AgentDefaultSettings(BaseModel):
    """Defines default settings for an agent. These settings control various aspects of the agent's behavior during operation."""

    temperature: float = 0.0
    """Temperature setting influencing the randomness of the agent's responses. Higher values lead to more random responses."""

    top_p: float = 1.0
    """Top-p sampling setting controlling the nucleus of the probability distribution to sample from."""
    
    repetition_penalty: float = 1.0
    """Penalty applied to discourage repetition in the agent's responses."""

    length_penalty: float = 1.0
    """Penalty for longer responses, encouraging more concise outputs."""

    presence_penalty: float = 0.0
    """Penalty applied based on the presence of certain words, influencing content generation."""

    frequency_penalty: float = 0.0
    """Penalty that decreases the likelihood of frequently used words in the agent's responses."""

    min_p: float = 0.01
    """Minimum probability threshold for including a word in the agent's response."""
