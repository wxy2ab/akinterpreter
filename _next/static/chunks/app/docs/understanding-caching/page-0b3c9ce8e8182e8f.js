(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[176,863,967,778,448,195,285,698,548,403,649,57,206,719,286,718,562,644,825,931],{68:function(e,t,l){Promise.resolve().then(l.t.bind(l,231,23)),Promise.resolve().then(l.bind(l,1884)),Promise.resolve().then(l.bind(l,7805)),Promise.resolve().then(l.bind(l,229)),Promise.resolve().then(l.bind(l,7125))},1884:function(e,t,l){"use strict";l.d(t,{DocsHeader:function(){return r}});var s=l(7437),n=l(6463),i=l(4110);function r(e){let{title:t}=e,l=(0,n.usePathname)(),r=i.G.find(e=>e.links.find(e=>e.href===l));return t||r?(0,s.jsxs)("header",{className:"mb-9 space-y-1",children:[r&&(0,s.jsx)("p",{className:"font-display text-sm font-medium text-sky-500",children:r.title}),t&&(0,s.jsx)("h1",{className:"font-display text-3xl tracking-tight text-slate-900 dark:text-white",children:t})]}):null}},7805:function(e,t,l){"use strict";l.d(t,{Fence:function(){return r}});var s=l(7437),n=l(2265),i=l(373);function r(e){let{children:t,language:l}=e;return(0,s.jsx)(i.y$,{code:t.trimEnd(),language:l,theme:{plain:{},styles:[]},children:e=>{let{className:t,style:l,tokens:i,getTokenProps:r}=e;return(0,s.jsx)("pre",{className:t,style:l,children:(0,s.jsx)("code",{children:i.map((e,t)=>(0,s.jsxs)(n.Fragment,{children:[e.filter(e=>!e.empty).map((e,t)=>(0,s.jsx)("span",{...r({token:e})},t)),"\n"]},t))})})}})}},229:function(e,t,l){"use strict";l.d(t,{PrevNextLinks:function(){return c}});var s=l(7437),n=l(7138),i=l(6463),r=l(4839),a=l(4110);function d(e){return(0,s.jsx)("svg",{viewBox:"0 0 16 16","aria-hidden":"true",...e,children:(0,s.jsx)("path",{d:"m9.182 13.423-1.17-1.16 3.505-3.505H3V7.065h8.517l-3.506-3.5L9.181 2.4l5.512 5.511-5.511 5.512Z"})})}function o(e){let{title:t,href:l,dir:i="next",...a}=e;return(0,s.jsxs)("div",{...a,children:[(0,s.jsx)("dt",{className:"font-display text-sm font-medium text-slate-900 dark:text-white",children:"next"===i?"Next":"Previous"}),(0,s.jsx)("dd",{className:"mt-1",children:(0,s.jsxs)(n.default,{href:l,className:(0,r.Z)("flex items-center gap-x-1 text-base font-semibold text-slate-500 hover:text-slate-600 dark:text-slate-400 dark:hover:text-slate-300","previous"===i&&"flex-row-reverse"),children:[t,(0,s.jsx)(d,{className:(0,r.Z)("h-4 w-4 flex-none fill-current","previous"===i&&"-scale-x-100")})]})})]})}function c(){let e=(0,i.usePathname)(),t=a.G.flatMap(e=>e.links),l=t.findIndex(t=>t.href===e),n=l>-1?t[l-1]:null,r=l>-1?t[l+1]:null;return r||n?(0,s.jsxs)("dl",{className:"mt-12 flex border-t border-slate-200 pt-6 dark:border-slate-800",children:[n&&(0,s.jsx)(o,{dir:"previous",...n}),r&&(0,s.jsx)(o,{className:"ml-auto text-right",...r})]}):null}},7125:function(e,t,l){"use strict";l.d(t,{TableOfContents:function(){return a}});var s=l(7437),n=l(2265),i=l(7138),r=l(4839);function a(e){let{tableOfContents:t}=e,[l,a]=(0,n.useState)(t[0]?.id),d=(0,n.useCallback)(e=>e.flatMap(e=>[e.id,...e.children.map(e=>e.id)]).map(e=>{let t=document.getElementById(e);if(!t)return null;let l=parseFloat(window.getComputedStyle(t).scrollMarginTop);return{id:e,top:window.scrollY+t.getBoundingClientRect().top-l}}).filter(e=>null!==e),[]);function o(e){return e.id===l||!!e.children&&e.children.findIndex(o)>-1}return(0,n.useEffect)(()=>{if(0===t.length)return;let e=d(t);function l(){let t=window.scrollY,l=e[0].id;for(let s of e)if(t>=s.top-10)l=s.id;else break;a(l)}return window.addEventListener("scroll",l,{passive:!0}),l(),()=>{window.removeEventListener("scroll",l)}},[d,t]),(0,s.jsx)("div",{className:"hidden xl:sticky xl:top-[4.75rem] xl:-mr-6 xl:block xl:h-[calc(100vh-4.75rem)] xl:flex-none xl:overflow-y-auto xl:py-16 xl:pr-6",children:(0,s.jsx)("nav",{"aria-labelledby":"on-this-page-title",className:"w-56",children:t.length>0&&(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)("h2",{id:"on-this-page-title",className:"font-display text-sm font-medium text-slate-900 dark:text-white",children:"On this page"}),(0,s.jsx)("ol",{role:"list",className:"mt-4 space-y-3 text-sm",children:t.map(e=>(0,s.jsxs)("li",{children:[(0,s.jsx)("h3",{children:(0,s.jsx)(i.default,{href:`#${e.id}`,className:(0,r.Z)(o(e)?"text-sky-500":"font-normal text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"),children:e.title})}),e.children.length>0&&(0,s.jsx)("ol",{role:"list",className:"mt-2 space-y-3 pl-5 text-slate-500 dark:text-slate-400",children:e.children.map(e=>(0,s.jsx)("li",{children:(0,s.jsx)(i.default,{href:`#${e.id}`,className:o(e)?"text-sky-500":"hover:text-slate-600 dark:hover:text-slate-300",children:e.title})},e.id))})]},e.id))})]})})})}},4110:function(e,t,l){"use strict";l.d(t,{G:function(){return s}});let s=[{title:"使用手册",links:[{title:"上手使用",href:"/"},{title:"推荐安装",href:"/docs/installation"},{title:" 无python安装",href:"/docs/non_python_install"}]},{title:"配置",links:[{title:"选择LLM API",href:"/docs/select_llm_api"},{title:"配置API_KEY",href:"/docs/setting_api_keys"},{title:"安装依赖",href:"/docs/requirement_install"}]},{title:"使用",links:[{title:"特性",href:"/docs/featrue"},{title:"指令",href:"/docs/instruction"}]},{title:"技巧",links:[{title:"使用gpt4o",href:"/docs/use_outside"}]},{title:"关联项目",links:[{title:"akshare",href:"/docs/akshare"},{title:"ak_code_library",href:"/docs/ak_code_library"}]},{title:"文档模板",links:[{title:"文档模板",href:"/docs/docs_template"}]}]}},function(e){e.O(0,[231,55,971,23,744],function(){return e(e.s=68)}),_N_E=e.O()}]);