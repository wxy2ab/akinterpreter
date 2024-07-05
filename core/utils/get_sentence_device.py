def get_sentence_transformer_device()->str:
    """
    确定 SentenceTransformer 的最合适设备，优先考虑
    GPU 类设备（'cuda'、'mps'、'npu'），如果不可用则回退到 'cpu'。

    返回：
        str: 设备标识符（'cuda'、'mps'、'npu' 或 'cpu'）。
    """

    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"  # 如果 CUDA 可用，返回 "cuda"

        # 检查 macOS 上的 MPS（Metal Performance Shaders）
        if torch.backends.mps.is_available():
            return "mps"  # 如果 MPS 可用，返回 "mps"

        # 检查 NPU（神经处理单元）
        if torch.backends.mps.is_built():  # 假设 NPU 支持由 MPS 构建指示
            return "npu"  # 如果 NPU 可用，返回 "npu"

    except (ImportError, AttributeError):
        pass  # 如果 PyTorch 未安装或不支持后端，忽略错误

    return "cpu"  # 如果未找到类 GPU 设备，则默认为 CPU