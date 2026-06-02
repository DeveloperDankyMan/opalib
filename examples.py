"""
Complete Usage Guide and Examples
Demonstrates all features of the Opalib AI Framework
"""

from src.opalib.framework import UnifiedAIFramework, LocalModelConfig
from src.opalib.ai import AgentConversation, create_agent as create_pollinations_agent


def example_1_create_local_model():
    """Example 1: Create and use a local AI model."""
    print("=" * 60)
    print("Example 1: Creating a Local AI Model")
    print("=" * 60)
    
    # Initialize framework
    framework = UnifiedAIFramework(device="auto")
    
    # Create a small transformer model
    model = framework.create_model(
        name="tiny_gpt",
        model_type="transformer",
        vocab_size=5000,
        embedding_dim=128,
        hidden_dim=256,
        num_layers=2,
        num_heads=4,
        max_seq_length=256
    )
    
    # Generate text
    prompt = "Hello, how are you?"
    response = model.generate(prompt, max_tokens=30)
    print(f"\nPrompt: {prompt}")
    print(f"Response: {response}")
    
    # Get model statistics
    stats = model.get_stats()
    print(f"\nModel Stats: {stats}")


def example_2_create_local_agent():
    """Example 2: Create and chat with a local AI agent."""
    print("\n" + "=" * 60)
    print("Example 2: Creating a Local AI Agent")
    print("=" * 60)
    
    # Initialize framework
    framework = UnifiedAIFramework(device="auto")
    
    # Create model
    model = framework.create_model(
        name="assistant_model",
        vocab_size=3000,
        embedding_dim=96,
        hidden_dim=192,
        num_layers=2,
        num_heads=4,
    )
    
    # Create agent
    agent = framework.create_agent(
        name="helpful_assistant",
        model_name="assistant_model",
        system_prompt="You are a helpful and friendly AI assistant."
    )
    
    # Chat with agent
    messages = [
        "What is machine learning?",
        "Explain neural networks",
        "What is an attention mechanism?"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        response = agent.chat(message, max_tokens=50)
        print(f"Agent: {response}")
    
    # View conversation history
    print("\n--- Conversation History ---")
    for entry in agent.get_history():
        print(f"{entry['role'].upper()}: {entry['content'][:100]}...")


def example_3_multiple_agents_local():
    """Example 3: Create multiple local agents with different personalities."""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Local Agents with Different Personalities")
    print("=" * 60)
    
    framework = UnifiedAIFramework(device="auto")
    
    # Create one model for all agents (shared)
    model = framework.create_model(
        name="shared_model",
        vocab_size=2000,
        embedding_dim=64,
        hidden_dim=128,
        num_layers=1,
    )
    
    # Create agents with different personalities
    agent1 = framework.create_agent(
        name="scientist",
        model_name="shared_model",
        system_prompt="You are a physicist. Respond with scientific accuracy."
    )
    
    agent2 = framework.create_agent(
        name="poet",
        model_name="shared_model",
        system_prompt="You are a poet. Respond creatively and poetically."
    )
    
    agent3 = framework.create_agent(
        name="comedian",
        model_name="shared_model",
        system_prompt="You are a comedian. Make your responses funny and witty."
    )
    
    # All chat about the same topic
    topic = "What is artificial intelligence?"
    
    print(f"\nTopic: {topic}\n")
    
    response1 = agent1.chat(topic, max_tokens=40)
    print(f"Scientist: {response1}\n")
    
    response2 = agent2.chat(topic, max_tokens=40)
    print(f"Poet: {response2}\n")
    
    response3 = agent3.chat(topic, max_tokens=40)
    print(f"Comedian: {response3}\n")


def example_4_save_and_load_model():
    """Example 4: Save and load a local model."""
    print("\n" + "=" * 60)
    print("Example 4: Save and Load Models")
    print("=" * 60)
    
    framework = UnifiedAIFramework()
    
    # Create model
    model = framework.create_model(
        name="saveable_model",
        vocab_size=1000,
        embedding_dim=64,
        hidden_dim=128,
        num_layers=1,
    )
    
    # Save model
    save_path = "models/my_model.pt"
    model.save(save_path)
    print(f"Model saved to: {save_path}")
    
    # Load model
    loaded_model = model.load(save_path)
    print(f"Model loaded from: {save_path}")
    
    # Test loaded model
    response = loaded_model.generate("Hello", max_tokens=20)
    print(f"Generated text from loaded model: {response}")


def example_5_model_quantization():
    """Example 5: Quantize model for efficiency."""
    print("\n" + "=" * 60)
    print("Example 5: Model Quantization")
    print("=" * 60)
    
    framework = UnifiedAIFramework()
    
    # Create model
    model = framework.create_model(
        name="quantized_model",
        vocab_size=1000,
        embedding_dim=64,
        hidden_dim=128,
    )
    
    print("Original model memory usage:")
    stats = model.get_stats()
    print(f"Memory: {stats['memory_usage']}")
    
    # Quantize to int8
    model.quantize(bits=8)
    print("\nModel quantized to int8")
    
    print("After quantization memory usage:")
    stats = model.get_stats()
    print(f"Memory: {stats['memory_usage']}")


def example_6_hybrid_agents():
    """Example 6: Hybrid approach - mix local and cloud agents."""
    print("\n" + "=" * 60)
    print("Example 6: Hybrid Local + Cloud Agents")
    print("=" * 60)
    
    # Local agent
    local_framework = UnifiedAIFramework(device="cpu")
    local_model = local_framework.create_model(
        name="local",
        vocab_size=1000,
        embedding_dim=48,
        hidden_dim=96,
    )
    local_agent = local_framework.create_agent(
        name="local_ai",
        model_name="local",
    )
    
    # Cloud agent (using Pollinations)
    from src.opalib.ai import create_agent as create_cloud_agent
    
    cloud_agent = create_cloud_agent(
        name="CloudAssistant",
        system_prompt="You are a cloud-based AI assistant."
    )
    
    print("Local Agent Response:")
    local_response = local_agent.chat("What is AI?", max_tokens=30)
    print(f"Response: {local_response}\n")
    
    print("Cloud Agent Response:")
    cloud_response = cloud_agent.add_message("user", "What is AI?")
    print(f"Response: Ready for cloud processing")


def example_7_benchmark():
    """Example 7: Benchmark model performance."""
    print("\n" + "=" * 60)
    print("Example 7: Model Benchmarking")
    print("=" * 60)
    
    framework = UnifiedAIFramework(device="auto")
    
    # Create model
    model = framework.create_model(
        name="benchmark_model",
        vocab_size=1000,
        embedding_dim=64,
        hidden_dim=128,
    )
    
    # Benchmark
    results = model.benchmark(num_tokens=100)
    print(f"\nBenchmark Results:")
    print(f"  Device: {results['device']}")
    print(f"  Tokens Generated: {results['tokens_generated']}")
    print(f"  Time (seconds): {results['time_seconds']:.4f}")
    print(f"  Tokens/Second: {results['tokens_per_second']:.2f}")


def example_8_framework_overview():
    """Example 8: Full framework overview."""
    print("\n" + "=" * 60)
    print("Example 8: Framework Overview")
    print("=" * 60)
    
    framework = UnifiedAIFramework(device="auto")
    
    # Create multiple models
    print("\nCreating models...")
    for i in range(3):
        framework.create_model(
            name=f"model_{i}",
            vocab_size=1000 + i * 500,
            embedding_dim=32 + i * 16,
            hidden_dim=64 + i * 32,
        )
    
    # Create multiple agents
    print("Creating agents...")
    for i, model_name in enumerate(framework.list_models()):
        framework.create_agent(
            name=f"agent_{i}",
            model_name=model_name,
        )
    
    # Display overview
    print(f"\nFramework Overview:")
    print(f"  Available Models: {framework.list_models()}")
    print(f"  Available Agents: {framework.list_agents()}")
    print(f"  Device: {framework.device}")


def example_9_advanced_tokenization():
    """Example 9: Advanced tokenization."""
    print("\n" + "=" * 60)
    print("Example 9: Advanced Tokenization")
    print("=" * 60)
    
    from src.opalib.tokenizer import BPETokenizer
    
    tokenizer = BPETokenizer(vocab_size=1000)
    
    # Train tokenizer
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Neural networks are inspired by biological neurons"
    ]
    
    print("Training tokenizer...")
    tokenizer.train(texts, num_merges=100)
    
    # Encode text
    text = "Hello world"
    tokens = tokenizer.encode(text)
    print(f"\nOriginal text: {text}")
    print(f"Encoded tokens: {tokens}")
    
    # Decode tokens
    decoded = tokenizer.decode(tokens)
    print(f"Decoded text: {decoded}")
    
    # Save/load tokenizer
    tokenizer.save("tokenizers/my_tokenizer.json")
    print("\nTokenizer saved!")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  OPALIB: Complete Local AI Framework Examples  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        example_1_create_local_model()
        example_2_create_local_agent()
        example_3_multiple_agents_local()
        example_4_save_and_load_model()
        example_5_model_quantization()
        example_6_hybrid_agents()
        example_7_benchmark()
        example_8_framework_overview()
        example_9_advanced_tokenization()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
