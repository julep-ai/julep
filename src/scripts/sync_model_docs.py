#!/usr/bin/env python3
"""
Sync model information from litellm-config.yaml to documentation.

This script reads the configured models from litellm-config.yaml,
fetches pricing/feature data from LiteLLM's GitHub repository,
and updates the supported-models.mdx file.

The pricing data is fetched from:
https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
import yaml
import urllib.request
import urllib.error


# Cost tier classification based on input token price
def classify_cost_tier(input_cost_per_token: float) -> str:
    """Classify model cost tier based on input token cost."""
    if input_cost_per_token == 0:
        return "Free"
    elif input_cost_per_token < 0.0000005:  # $0.50 per 1M tokens
        return "Budget"
    elif input_cost_per_token < 0.000002:   # $2.00 per 1M tokens
        return "Standard"
    elif input_cost_per_token < 0.00001:    # $10.00 per 1M tokens
        return "Premium"
    else:
        return "Enterprise"


def normalize_model_name(model_name: str) -> str:
    """Normalize model name to match between configs."""
    # Remove provider prefixes
    normalized = re.sub(r'^(openai/|gemini/|anthropic/|groq/|openrouter/|cerebras/|voyage/|vertex_ai/)', '', model_name)
    
    # Handle special cases
    if normalized.startswith("claude-"):
        # Convert claude names to match pricing file format
        normalized = normalized.replace("claude-3-5-", "claude-3.5-")
        normalized = normalized.replace("claude-3-7-", "claude-3.7-")
    
    return normalized


def find_model_in_pricing_data(model_name: str, litellm_model: str, pricing_data: Dict) -> Optional[Dict]:
    """Find model in pricing data using various matching strategies."""
    # Direct matches to try
    candidates = [
        model_name,
        litellm_model,
        normalize_model_name(model_name),
        normalize_model_name(litellm_model),
    ]
    
    # Add provider-specific variations
    if "/" in litellm_model:
        provider, model_part = litellm_model.split("/", 1)
        candidates.extend([
            model_part,
            f"{provider}/{normalize_model_name(model_part)}",
        ])
    
    # Try each candidate
    for candidate in candidates:
        if candidate in pricing_data:
            return pricing_data[candidate]
    
    # Try partial matching for specific patterns
    for key in pricing_data:
        if any(candidate in key or key in candidate for candidate in candidates):
            return pricing_data[key]
    
    return None


def extract_models_from_config(config_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract model configurations from litellm-config.yaml."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    models = []
    embedding_models = []
    
    for model_config in config.get('model_list', []):
        model_name = model_config.get('model_name', '')
        litellm_params = model_config.get('litellm_params', {})
        litellm_model = litellm_params.get('model', '')
        tags = litellm_params.get('tags', [])
        
        # Check if it's an embedding model
        is_embedding = ('embedding' in model_name.lower() or 'embedding' in litellm_model.lower() or
                       model_name.startswith('text-embedding') or model_name.startswith('voyage') or
                       '/bge-' in litellm_model or '/gte-' in litellm_model)
        
        model_data = {
            'name': model_name,
            'litellm_model': litellm_model,
            'provider': litellm_model.split('/')[0] if '/' in litellm_model else 'unknown',
            'is_free': 'free' in tags,
            'tags': tags
        }
        
        if is_embedding:
            embedding_models.append(model_data)
        else:
            models.append(model_data)
    
    return models, embedding_models


def enrich_model_data(models: List[Dict], pricing_data: Dict) -> List[Dict]:
    """Enrich model data with pricing and feature information."""
    enriched = []
    
    for model in models:
        model_info = find_model_in_pricing_data(model['name'], model['litellm_model'], pricing_data)
        
        if model_info:
            model['context_window'] = model_info.get('max_input_tokens', model_info.get('max_tokens', 'Unknown'))
            model['max_output'] = model_info.get('max_output_tokens', 'Unknown')
            model['supports_tools'] = model_info.get('supports_function_calling', False)
            model['supports_vision'] = model_info.get('supports_vision', False)
            model['supports_audio'] = model_info.get('supports_audio_input', False) or model_info.get('supports_audio_output', False)
            model['supports_prompt_caching'] = model_info.get('supports_prompt_caching', False)
            
            # Calculate cost tier
            input_cost = model_info.get('input_cost_per_token', 0)
            model['cost_tier'] = classify_cost_tier(input_cost)
        else:
            # Default values for models not in pricing data
            model['context_window'] = 'Unknown'
            model['max_output'] = 'Unknown'
            model['supports_tools'] = 'Unknown'
            model['supports_vision'] = False
            model['supports_audio'] = False
            model['supports_prompt_caching'] = False
            model['cost_tier'] = 'Unknown'
        
        enriched.append(model)
    
    return enriched


def generate_model_table(models: List[Dict]) -> str:
    """Generate markdown table for models grouped by provider."""
    # Group models by provider
    providers = {}
    provider_map = {
        'openai': 'OpenAI',
        'anthropic': 'Anthropic', 
        'gemini': 'Google',
        'groq': 'Groq',
        'openrouter': 'OpenRouter',
        'cerebras': 'Cerebras',
        'unknown': 'Anthropic'  # Claude models show as unknown
    }
    
    for model in models:
        provider_key = model['provider'].lower()
        provider_name = provider_map.get(provider_key, provider_key.title())
        
        # Special handling for models
        if model['name'].startswith('claude'):
            provider_name = 'Anthropic'
        elif model['name'].startswith('amazon/'):
            provider_name = 'Amazon Nova'
        
        if provider_name not in providers:
            providers[provider_name] = []
        providers[provider_name].append(model)
    
    # Define provider order to match existing doc
    provider_order = ['Anthropic', 'Google', 'OpenAI', 'Groq', 'OpenRouter', 'Cerebras', 'Amazon Nova']
    
    tables = []
    for provider in provider_order:
        if provider not in providers:
            continue
            
        provider_models = sorted(providers[provider], key=lambda x: x['name'])
        
        # Generate markdown table matching existing format
        table = f"\n### {provider}\n\n"
        table += f"Here are the {provider} models supported by Julep:\n\n"
        table += "| Model Name | Context Window | Max Output | Tool Calling | Vision | Audio | Caching | Cost Tier |\n"
        table += "|------------|----------------|------------|--------------|--------|-------|---------|----------|\n"
        
        for model in provider_models:
            # Format context window
            if isinstance(model['context_window'], int):
                if model['context_window'] >= 1000000:
                    context = f"{model['context_window'] // 1000000}M tokens"
                elif model['context_window'] >= 1000:
                    context = f"{model['context_window'] // 1000}K tokens"
                else:
                    context = f"{model['context_window']} tokens"
            else:
                context = "Unknown"
            
            # Format max output
            if isinstance(model['max_output'], int):
                if model['max_output'] >= 1000000:
                    max_out = f"{model['max_output'] // 1000000}M tokens"
                elif model['max_output'] >= 1000:
                    max_out = f"{model['max_output'] // 1000}K tokens"
                else:
                    max_out = f"{model['max_output']} tokens"
            else:
                max_out = "Unknown"
            
            # Format boolean support columns
            tools = "✅" if model['supports_tools'] else "❌" if model['supports_tools'] is False else "?"
            vision = "✅" if model['supports_vision'] else "❌"
            audio = "✅" if model['supports_audio'] else "❌"
            caching = "✅" if model['supports_prompt_caching'] else "❌"
            
            table += f"| {model['name']} | {context} | {max_out} | {tools} | {vision} | {audio} | {caching} | {model['cost_tier']} |\n"
        
        tables.append(table)
    
    # Add any remaining providers not in the order
    remaining = [p for p in providers if p not in provider_order]
    for provider in sorted(remaining):
        provider_models = sorted(providers[provider], key=lambda x: x['name'])
        
        table = f"\n### {provider}\n\n"
        table += f"Here are the {provider} models supported by Julep:\n\n"
        table += "| Model Name | Context Window | Max Output | Tool Calling | Vision | Audio | Caching | Cost Tier |\n"
        table += "|------------|----------------|------------|--------------|--------|-------|---------|----------|\n"
        
        for model in provider_models:
            if isinstance(model['context_window'], int):
                if model['context_window'] >= 1000000:
                    context = f"{model['context_window'] // 1000000}M tokens"
                elif model['context_window'] >= 1000:
                    context = f"{model['context_window'] // 1000}K tokens"
                else:
                    context = f"{model['context_window']} tokens"
            else:
                context = "Unknown"
            
            # Format max output
            if isinstance(model['max_output'], int):
                if model['max_output'] >= 1000000:
                    max_out = f"{model['max_output'] // 1000000}M tokens"
                elif model['max_output'] >= 1000:
                    max_out = f"{model['max_output'] // 1000}K tokens"
                else:
                    max_out = f"{model['max_output']} tokens"
            else:
                max_out = "Unknown"
            
            # Format boolean support columns
            tools = "✅" if model['supports_tools'] else "❌" if model['supports_tools'] is False else "?"
            vision = "✅" if model['supports_vision'] else "❌"
            audio = "✅" if model['supports_audio'] else "❌"
            caching = "✅" if model['supports_prompt_caching'] else "❌"
            
            table += f"| {model['name']} | {context} | {max_out} | {tools} | {vision} | {audio} | {caching} | {model['cost_tier']} |\n"
        
        tables.append(table)
    
    return "\n".join(tables)


def generate_embedding_table(embedding_models: List[Dict]) -> str:
    """Generate markdown table for embedding models."""
    if not embedding_models:
        return ""
    
    table = "\n### Embedding\n\n"
    table += "Here are the embedding models supported by Julep:\n\n"
    table += "| Model Name | Embedding Dimensions |\n"
    table += "|------------|---------------------|\n"
    
    for model in sorted(embedding_models, key=lambda x: x['name']):
        # All embedding models in Julep use 1024 dimensions as noted in the original doc
        dimensions = "1024"
        
        table += f"| {model['name']} | {dimensions} |\n"
    
    table += "\n<Info>\n"
    table += "Though the models mention above support different embedding dimensions, Julep uses fixed 1024 dimensions for all embedding models for now. We plan to support different dimensions in the future.\n"
    table += "</Info>\n"
    
    return table




def update_documentation(doc_path: Path, model_section: str):
    """Update the documentation file with new model information."""
    with open(doc_path, 'r') as f:
        content = f.read()
    
    # Find the Available Models section
    available_models_start = content.find("## Available Models")
    if available_models_start == -1:
        print("Error: Could not find '## Available Models' section")
        return
    
    # Find where to stop - look for the next ## section after Available Models
    # This could be "## Supported Parameters" or any other section
    next_major_section = content.find("\n## ", available_models_start + 1)
    if next_major_section == -1:
        # If no next section found, replace to end of file
        end_marker = len(content)
    else:
        end_marker = next_major_section
    
    # Extract the part before models
    before_models = content[:available_models_start]
    
    # Find where the actual model listings start
    # Look for the first provider heading (could be ### or #)
    import re
    
    # Find the first provider section (### Anthropic, ### Google, etc.)
    first_provider_match = re.search(r'\n###?\s+(Anthropic|Google|OpenAI|Groq|OpenRouter|Cerebras|Amazon)', 
                                     content[available_models_start:end_marker])
    
    if first_provider_match:
        models_content_start = available_models_start + first_provider_match.start()
    else:
        # If no provider found, look for where tip/info boxes end
        # Find the last </Tip> or </Info> tag
        last_tip = content.rfind("</Tip>", available_models_start, end_marker)
        last_info = content.rfind("</Info>", available_models_start, end_marker)
        last_tag = max(last_tip, last_info)
        if last_tag > -1:
            # Find the newline after the tag
            newline_after = content.find("\n", last_tag)
            models_content_start = newline_after + 1
        else:
            # Fallback: just use some offset after the section header
            models_content_start = available_models_start + len("## Available Models\n\n")
    
    # Extract the header part (with info/tip boxes)
    models_header = content[available_models_start:models_content_start]
    
    # Extract the part after models
    after_models = content[end_marker:]
    
    # Construct new content
    new_content = before_models + models_header + model_section + after_models
    
    with open(doc_path, 'w') as f:
        f.write(new_content)


def fetch_pricing_data() -> Dict:
    """Fetch pricing data from LiteLLM GitHub repository."""
    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    
    try:
        print(f"Fetching pricing data from {url}...")
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        print("✅ Successfully fetched pricing data")
        return data
    except urllib.error.URLError as e:
        print(f"❌ Error fetching pricing data: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing pricing data: {e}")
        raise


def main():
    """Main function to sync model documentation."""
    # Define paths - handle different execution contexts
    script_path = Path(__file__).resolve()
    
    # Check if we're in src/scripts or being run from elsewhere
    if script_path.parent.name == "scripts" and script_path.parent.parent.name == "src":
        # Running from src/scripts/
        project_root = script_path.parent.parent.parent
    else:
        # Running from somewhere else, try to find project root
        current = script_path.parent
        while current != current.parent:
            if (current / "src" / "llm-proxy").exists():
                project_root = current
                break
            current = current.parent
        else:
            # Fallback to relative paths
            project_root = Path.cwd()
    
    config_path = project_root / "src" / "llm-proxy" / "litellm-config.yaml"
    doc_path = project_root / "documentation" / "integrations" / "supported-models.mdx"
    
    # Check files exist
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return 1
    
    if not doc_path.exists():
        print(f"Error: Documentation file not found at {doc_path}")
        return 1
    
    # Fetch pricing data from GitHub
    try:
        pricing_data = fetch_pricing_data()
    except Exception as e:
        print(f"Failed to fetch pricing data: {e}")
        return 1
    
    # Extract and enrich model data
    print("Extracting models from litellm config...")
    models, embedding_models = extract_models_from_config(config_path)
    print(f"Found {len(models)} models and {len(embedding_models)} embedding models")
    
    print("Enriching model data with pricing information...")
    enriched_models = enrich_model_data(models, pricing_data)
    
    # Generate documentation
    print("Generating model documentation...")
    model_section = generate_model_table(enriched_models)
    embedding_section = generate_embedding_table(embedding_models)
    
    # Combine sections
    full_section = model_section + "\n" + embedding_section
    
    # Update documentation file
    print("Updating documentation file...")
    update_documentation(doc_path, full_section)
    
    print("✅ Documentation updated successfully!")
    
    # Print summary
    cost_tiers = {}
    for model in enriched_models:
        tier = model['cost_tier']
        cost_tiers[tier] = cost_tiers.get(tier, 0) + 1
    
    print("\nModel Summary:")
    print(f"Total models: {len(enriched_models)}")
    print(f"Embedding models: {len(embedding_models)}")
    for tier, count in sorted(cost_tiers.items()):
        print(f"  {tier}: {count} models")
    
    return 0


if __name__ == "__main__":
    exit(main())