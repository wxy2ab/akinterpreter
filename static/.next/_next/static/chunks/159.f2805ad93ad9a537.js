"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[159],{3159:function(e,t,a){a.r(t),a.d(t,{default:function(){return E}});var s=a(57437),r=a(2265),l=a(37270),n=a(95750),i=a(49354),o=a(19425);let c=(0,a(12218).j)("inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors hover:bg-slate-100 hover:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-slate-100 data-[state=on]:text-slate-900 dark:ring-offset-slate-950 dark:hover:bg-slate-800 dark:hover:text-slate-400 dark:focus-visible:ring-slate-300 dark:data-[state=on]:bg-slate-800 dark:data-[state=on]:text-slate-50",{variants:{variant:{default:"bg-transparent",outline:"border border-slate-200 bg-transparent hover:bg-slate-100 hover:text-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-50"},size:{default:"h-10 px-3",sm:"h-9 px-2.5",lg:"h-11 px-5"}},defaultVariants:{variant:"default",size:"default"}});r.forwardRef((e,t)=>{let{className:a,variant:r,size:l,...n}=e;return(0,s.jsx)(o.f,{ref:t,className:(0,i.cn)(c({variant:r,size:l,className:a})),...n})}).displayName=o.f.displayName;let d=r.createContext({size:"default",variant:"default"}),u=r.forwardRef((e,t)=>{let{className:a,variant:r,size:l,children:o,...c}=e;return(0,s.jsx)(n.fC,{ref:t,className:(0,i.cn)("flex items-center justify-center gap-1",a),...c,children:(0,s.jsx)(d.Provider,{value:{variant:r,size:l},children:o})})});u.displayName=n.fC.displayName;let f=r.forwardRef((e,t)=>{let{className:a,children:l,variant:o,size:u,...f}=e,m=r.useContext(d);return(0,s.jsx)(n.ck,{ref:t,className:(0,i.cn)(c({variant:m.variant||o,size:m.size||u}),a),...f,children:l})});f.displayName=n.ck.displayName;var m=a(6785),h=a(63775),p=a(50197);a(10715);var g=a(83644),y=a(7746);let x={custom:e=>{let{data:t}=e;return(0,s.jsxs)("div",{className:"px-4 py-2 shadow-md rounded-md bg-gray-800 border-2 border-gray-600 text-white w-[300px]",children:[(0,s.jsx)("div",{className:"text-lg font-bold",children:t.title}),(0,s.jsx)("hr",{className:"my-2 border-gray-600"}),(0,s.jsx)("div",{dangerouslySetInnerHTML:{__html:t.content},className:"text-sm"})]})}},v=(e,t)=>({nodes:e.map((e,t)=>{let a;return a="query_summary"===e.id?0:"1"===e.id?250:50+(t-1)*350+200,{...e,position:{x:0,y:a}}}),edges:t}),b=e=>{let{initialNodes:t,initialEdges:a}=e,{fitView:l}=(0,m._K)(),[n,i]=(0,r.useState)(t),[o,c]=(0,r.useState)(a);(0,r.useEffect)(()=>{i(t),c(a)},[t,a]);let d=(0,r.useCallback)(e=>i(t=>(0,m.Fb)(e,t)),[i]),u=(0,r.useCallback)(e=>c(t=>(0,m.yn)(e,t)),[c]),f=(0,r.useCallback)(e=>c(t=>(0,m.Z_)(e,t)),[c]);return(0,r.useEffect)(()=>{l({padding:.2})},[l,n,o]),(0,s.jsxs)(m.x$,{nodes:n,edges:o,onNodesChange:d,onEdgesChange:u,onConnect:f,nodeTypes:x,fitView:!0,minZoom:.1,maxZoom:1.5,children:[(0,s.jsx)(h.Z,{}),(0,s.jsx)(p.A,{})]})};var j=e=>{let{initialJson:t,onJsonChange:a}=e,[n,i]=(0,r.useState)(JSON.stringify(t,null,2)),[o,c]=(0,r.useState)("flowchart");(0,r.useEffect)(()=>{i(JSON.stringify(t,null,2))},[t]);let d=(0,r.useMemo)(()=>{if("flowchart"!==o)return{nodes:[],edges:[]};try{let e=JSON.parse(n),t=[],a=[];return t.push({id:"query_summary",type:"custom",data:{title:"Query Summary",content:"<p>".concat(e.query_summary,"</p>")},position:{x:0,y:0},draggable:!0}),Array.isArray(e.steps)&&(e.steps.forEach((e,s)=>{let r=Object.entries(e).map(e=>{let[t,a]=e;return"\n              <div>\n                <strong>".concat(t,":</strong> \n                ").concat(Array.isArray(a)?a.join(", "):a,"\n              </div>\n            ")}).join('<hr class="my-2 border-gray-600" />');t.push({id:"".concat(e.step_number),type:"custom",data:{title:"Step ".concat(e.step_number),content:r},position:{x:0,y:0},draggable:!0}),0===s?a.push({id:"e-summary-".concat(s+1),source:"query_summary",target:"".concat(s+1),animated:!0,type:"smoothstep",markerEnd:{type:m.QZ.ArrowClosed}}):a.push({id:"e".concat(s,"-").concat(s+1),source:"".concat(s),target:"".concat(s+1),animated:!0,type:"smoothstep",markerEnd:{type:m.QZ.ArrowClosed}})}),t.push({id:"summary",type:"custom",data:{title:"分析总结",content:"<p>基于以上步骤的分析总结</p>"},position:{x:0,y:0},draggable:!0}),a.push({id:"e-last-summary",source:"".concat(e.steps.length),target:"summary",animated:!0,type:"smoothstep",markerEnd:{type:m.QZ.ArrowClosed}})),v(t,a)}catch(e){return console.error("Error parsing JSON:",e),{nodes:[],edges:[]}}},[n,o]);return(0,s.jsxs)("div",{className:"h-full w-full flex flex-col",children:[(0,s.jsx)("div",{className:"flex justify-end",children:(0,s.jsxs)(u,{type:"single",value:o,onValueChange:e=>{c(e)},className:"border-0",children:[(0,s.jsx)(f,{value:"flowchart","aria-label":"View as flowchart",children:(0,s.jsx)(g.Z,{className:"h-4 w-4"})}),(0,s.jsx)(f,{value:"json","aria-label":"View as JSON",children:(0,s.jsx)(y.Z,{className:"h-4 w-4"})})]})}),(0,s.jsx)("div",{className:"flex-grow overflow-auto",children:"json"===o?(0,s.jsx)(l.ZP,{height:"100%",defaultLanguage:"json",defaultValue:n,value:n,onChange:e=>{if(void 0!==e){i(e);try{let t=JSON.parse(e);a(t)}catch(e){console.error("Invalid JSON detected:",e)}}},theme:"vs-dark",options:{automaticLayout:!0,wordWrap:"on",formatOnType:!0}}):(0,s.jsx)(m.tV,{children:(0,s.jsx)(b,{initialNodes:d.nodes,initialEdges:d.edges})})})]})},N=a(7900),w=a(3074),k=a(79565),S=e=>{let{value:t,onChange:a,language:r}=e;return(0,s.jsx)("div",{style:{height:"100%",width:"100%",overflow:"auto"},children:(0,s.jsx)(N.ZP,{value:t,height:"100%",extensions:[(0,w.Vs)()],theme:k.cL,onChange:e=>a(e),basicSetup:{lineNumbers:!0,highlightActiveLineGutter:!0,highlightSpecialChars:!0,foldGutter:!0,drawSelection:!0,dropCursor:!0,allowMultipleSelections:!0,indentOnInput:!0,syntaxHighlighting:!0,bracketMatching:!0,closeBrackets:!0,autocompletion:!0,rectangularSelection:!0,crosshairCursor:!0,highlightActiveLine:!0,highlightSelectionMatches:!0,closeBracketsKeymap:!0,defaultKeymap:!0,searchKeymap:!0,historyKeymap:!0,foldKeymap:!0,completionKeymap:!0,lintKeymap:!0},style:{fontSize:"16px"}})})},C=a(62447);let O=C.fC,_=r.forwardRef((e,t)=>{let{className:a,...r}=e;return(0,s.jsx)(C.aV,{ref:t,className:(0,i.cn)("inline-flex h-10 items-center justify-center rounded-md bg-slate-100 p-1 text-slate-500 dark:bg-slate-800 dark:text-slate-400",a),...r})});_.displayName=C.aV.displayName;let J=r.forwardRef((e,t)=>{let{className:a,...r}=e;return(0,s.jsx)(C.xz,{ref:t,className:(0,i.cn)("inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white data-[state=active]:text-slate-950 data-[state=active]:shadow-sm dark:ring-offset-slate-950 dark:focus-visible:ring-slate-300 dark:data-[state=active]:bg-slate-950 dark:data-[state=active]:text-slate-50",a),...r})});J.displayName=C.xz.displayName;let V=r.forwardRef((e,t)=>{let{className:a,...r}=e;return(0,s.jsx)(C.VY,{ref:t,className:(0,i.cn)("mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 dark:ring-offset-slate-950 dark:focus-visible:ring-slate-300",a),...r})});V.displayName=C.VY.displayName;var E=e=>{let{currentPlan:t,stepCodes:a,onPlanUpdate:l,onCodeUpdate:n}=e,[i,o]=(0,r.useState)("plan"),[c,d]=(0,r.useState)(null),u=(0,r.useRef)(null),f=e=>{if("object"==typeof e&&null!==e)return e;try{let t=JSON.parse(e);if("object"==typeof t&&null!==t)return t}catch(e){console.error("Invalid JSON string provided, using empty object as fallback.",e)}return{}},m=(0,r.useMemo)(()=>f(t),[t]);return(0,s.jsx)("div",{className:"h-full flex flex-col bg-gray-800",children:(0,s.jsxs)(O,{defaultValue:"plan",className:"w-full h-full flex flex-col",children:[(0,s.jsxs)(_,{className:"flex justify-start border-b border-gray-700 bg-gray-800",children:[(0,s.jsx)(J,{value:"plan",className:"px-4 py-2",children:"Plan"}),Object.keys(a).map((e,t)=>(0,s.jsxs)(J,{value:e,className:"px-4 py-2",children:["Step ",t+1]},e))]}),c&&(0,s.jsx)("div",{className:"error-message text-red-500 p-2",children:c}),(0,s.jsxs)("div",{className:"flex-grow overflow-hidden",children:[(0,s.jsx)(V,{value:"plan",className:"h-full",children:(0,s.jsx)("div",{className:"h-full p-4",children:(0,s.jsx)(j,{initialJson:m,onJsonChange:e=>{u.current&&clearTimeout(u.current),u.current=setTimeout(()=>{try{let t=f(e);l(t)}catch(e){d("Failed to update JSON. Please check the console for more details.")}},2e3)}},JSON.stringify(m))})}),Object.entries(a).map(e=>{let[t,a]=e;return(0,s.jsx)(V,{value:t,className:"h-full",children:(0,s.jsx)("div",{className:"h-full p-4",children:(0,s.jsx)(S,{value:a,onChange:e=>n(t,e),language:"python"})})},t)})]})]})})}}}]);