"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[437],{8437:function(e,t,l){l.r(t),l.d(t,{default:function(){return h}});var n=l(7437),o=l(2265),r=l(7270),a=e=>{let{initialJson:t,onJsonChange:l}=e,[a,i]=(0,o.useState)(JSON.stringify(t,null,2));return(0,o.useEffect)(()=>{i(JSON.stringify(t,null,2))},[t]),(0,n.jsx)(r.ZP,{height:"100%",defaultLanguage:"json",defaultValue:a,value:a,onChange:e=>{if(void 0!==e){i(e);try{let t=JSON.parse(e);l(t)}catch(e){console.error("Invalid JSON detected:",e)}}},theme:"vs-dark",options:{automaticLayout:!0,wordWrap:"on",formatOnType:!0}})},i=l(7900),s=l(3074),c=l(9565),u=e=>{let{value:t,onChange:l,language:o}=e;return(0,n.jsx)("div",{style:{height:"100%",width:"100%",overflow:"auto"},children:(0,n.jsx)(i.ZP,{value:t,height:"100%",extensions:[(0,s.Vs)()],theme:c.cL,onChange:e=>l(e),basicSetup:{lineNumbers:!0,highlightActiveLineGutter:!0,highlightSpecialChars:!0,foldGutter:!0,drawSelection:!0,dropCursor:!0,allowMultipleSelections:!0,indentOnInput:!0,syntaxHighlighting:!0,bracketMatching:!0,closeBrackets:!0,autocompletion:!0,rectangularSelection:!0,crosshairCursor:!0,highlightActiveLine:!0,highlightSelectionMatches:!0,closeBracketsKeymap:!0,defaultKeymap:!0,searchKeymap:!0,historyKeymap:!0,foldKeymap:!0,completionKeymap:!0,lintKeymap:!0},style:{fontSize:"16px"}})})},h=e=>{let{currentPlan:t,stepCodes:l,onPlanUpdate:r,onCodeUpdate:i}=e,[s,c]=(0,o.useState)("plan"),[h,d]=(0,o.useState)(null),p=(0,o.useRef)(null),g=e=>{if("object"==typeof e&&null!==e)return e;try{let t=JSON.parse(e);if("object"==typeof t&&null!==t)return t}catch(e){console.error("Invalid JSON string provided, using empty object as fallback.",e)}return{}},y=(0,o.useMemo)(()=>g(t),[t]),f={padding:"10px 15px",cursor:"pointer",backgroundColor:"#2d3748",color:"#a0aec0",border:"none",borderRadius:"5px 5px 0 0",marginRight:"5px"},x={...f,backgroundColor:"#4299e1",color:"white"};return(0,n.jsxs)("div",{style:{height:"100%",display:"flex",flexDirection:"column",backgroundColor:"#2d3748"},children:[(0,n.jsxs)("div",{style:{display:"flex",borderBottom:"1px solid #4a5568",padding:"10px"},children:[(0,n.jsx)("button",{style:"plan"===s?x:f,onClick:()=>c("plan"),children:"Plan"}),Object.keys(l).map((e,t)=>(0,n.jsxs)("button",{style:s===e?x:f,onClick:()=>c(e),children:["Step ",t+1]},e))]}),(0,n.jsxs)("div",{style:{height:"calc(100% - 50px)",overflowY:"auto",padding:"20px",backgroundColor:"#1a202c",color:"white"},children:[h&&(0,n.jsx)("div",{className:"error-message",children:h}),"plan"===s?(0,n.jsx)(a,{initialJson:y,onJsonChange:e=>{p.current&&clearTimeout(p.current),p.current=setTimeout(()=>{try{let t=g(e);r(t)}catch(e){d("Failed to update JSON. Please check the console for more details.")}},2e3)}},JSON.stringify(y)):(0,n.jsx)(u,{value:l[s],onChange:e=>i(s,e),language:"python"})]})]})}}}]);