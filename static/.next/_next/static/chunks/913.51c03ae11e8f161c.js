"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[913],{9913:function(e,t,r){r.r(t),r.d(t,{default:function(){return u}});var l=r(7437),s=r(2265),n=r(6648),a=r(6913),i=r(1003),c=e=>{let{type:t,content:r,isBot:s}=e;return(0,l.jsx)("div",{className:"max-w-3/4 ".concat(s?"ml-0 mr-auto":"ml-auto mr-0"),children:(0,l.jsx)("div",{className:"p-3 rounded-lg ".concat(s?"bg-gray-700 text-white":"bg-blue-500 text-white"," max-h-[80vh] overflow-y-auto"),children:(()=>{if("object"==typeof r)return(0,l.jsx)(a.Z,{language:"json",style:i.Z,children:JSON.stringify(r,null,2)});if("string"==typeof r){let e=r.replace(/^```(json|python)?\s*|\s*```$/g,"");try{let t=JSON.parse(e);return(0,l.jsx)(a.Z,{language:"json",style:i.Z,children:JSON.stringify(t,null,2)})}catch(e){}return e.includes("def ")||e.includes("import ")||e.includes("print(")?(0,l.jsx)(a.Z,{language:"python",style:i.Z,children:e}):e.split(/(\!\[.*?\]\(.*?\)|\[.*?\]\(.*?\))/).map((e,t)=>{if(e.startsWith("![")){let r=e.match(/\!\[(.*?)\]\((.*?)\)/);if(r)return(0,l.jsx)("div",{className:"relative w-full h-64 my-2",children:(0,l.jsx)(n.default,{src:r[2],alt:r[1],layout:"fill",objectFit:"contain"})},t)}else if(e.startsWith("[")){let r=e.match(/\[(.*?)\]\((.*?)\)/);if(r)return(0,l.jsx)("a",{href:r[2],target:"_blank",rel:"noopener noreferrer",className:"text-blue-500 hover:underline",children:r[1]},t)}return(0,l.jsx)("span",{children:e},t)})}return(0,l.jsx)("p",{className:"break-words whitespace-pre-wrap",children:String(r)})})()})})},o=r(2800),u=e=>{let{initialMessages:t}=e,[r,n]=(0,s.useState)(t),[a,i]=(0,s.useState)(""),[u,d]=(0,s.useState)(!1),[h,f]=(0,s.useState)(null),[p,g]=(0,s.useState)(null);(0,s.useRef)(null);let x=(0,s.useRef)(null),y=(0,s.useRef)(null),m=(0,s.useRef)(null);(0,s.useEffect)(()=>{(async()=>{f(await (0,o.MQ)())})()},[]),(0,s.useEffect)(()=>{j()},[a]);let j=()=>{if(y.current){y.current.style.height="auto";let e=y.current.scrollHeight,t=parseInt(getComputedStyle(y.current).lineHeight);y.current.style.height="".concat(Math.min(e,5*t),"px")}},b=(0,s.useCallback)(async e=>{if(e.trim()&&!u){n(t=>[...t,{type:"text",content:e,isBot:!1}]),i(""),d(!0);try{let t=await (0,o.bE)(e);g(t),m.current&&m.current.close();let r=(0,o.cE)(t);m.current=r,r.onmessage=e=>{if("[DONE]"===e.data)d(!1),r.close();else try{let t=JSON.parse(e.data);n(e=>{let r=e[e.length-1];if(!r||r.type!==t.type||!r.isBot)return[...e,{...t,isBot:!0}];{let l={...r,content:r.content+t.content};return[...e.slice(0,-1),l]}})}catch(e){console.error("Error parsing message:",e)}},r.onerror=e=>{console.error("EventSource failed:",e),r.close(),d(!1)}}catch(e){console.error("Error sending message:",e),d(!1)}}},[u]);return(0,l.jsxs)("div",{className:"flex flex-col h-full bg-gray-900 text-white",children:[(0,l.jsxs)("div",{className:"flex-grow overflow-y-auto p-4 space-y-4",children:[r.map((e,t)=>(0,l.jsx)(c,{type:e.type,content:e.content,isBot:e.isBot},t)),u&&(0,l.jsx)("p",{className:"italic text-gray-500",children:"\uD83E\uDD16在努力思考。。。"}),(0,l.jsx)("div",{ref:x})]}),(0,l.jsx)("div",{className:"flex-shrink-0 border-t border-gray-700 p-2",children:(0,l.jsxs)("div",{className:"flex items-center",children:[(0,l.jsx)("textarea",{ref:y,value:a,onChange:e=>i(e.target.value),onKeyDown:e=>{"Enter"!==e.key||e.shiftKey||(e.preventDefault(),b(a))},className:"flex-grow p-2 bg-gray-800 border border-gray-700 rounded-l-md resize-none",placeholder:"输入消息... (Shift+Enter 换行)",disabled:u,rows:1,style:{minHeight:"38px",maxHeight:"120px",overflow:"auto"}}),(0,l.jsx)("button",{onClick:()=>b(a),className:"p-2 bg-blue-600 text-white rounded-r-md h-[38px]",disabled:u,children:"发送"})]})})]})}}}]);