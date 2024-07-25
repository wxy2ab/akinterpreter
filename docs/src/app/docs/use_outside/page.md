---
title: 使用gpt4o
nextjs:
  metadata:
    title: 使用gpt4o
    description: 如何使用gpt4,gemini等api.
---

众所周知，openai gpt4o是无法直接在国内使用的，在这里有两个方法可以让大家使用到心心念念的gpt4o。

---

## 使用SimpleAzureClient

项目中包含两个gpt4o的封装，使用SimpleAzureClient 是可以在国内使用的，但是你需要去Azure上申请，Azure就是步骤稍微复杂。但是申请很容易。

### 使用check_proxy_running

你可能是一个懂科学，懂魔法的人(这些东西我肯定是不懂的)。   
这个时候你可能会有一个奇奇怪怪的地址，比如： 127.0.0.1  X  10809
这个时候，你就可以
```python
from core.utils.tsdata import check_proxy_running
check_proxy_running("127.0.0.1", 10809,'http')
```

把这个代码放在main.py 里面    
然后奇怪的事情可能就发生了。   

