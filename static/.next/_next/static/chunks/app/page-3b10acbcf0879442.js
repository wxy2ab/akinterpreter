(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[931],{3683:function(e,n,t){"use strict";var a=t(5652),s=t.n(a),o=t(8167),r=t.n(o)()(s());r.push([e.id,".react-tabs__tab-list {\n    border-bottom: 1px solid #4a5568;\n    margin: 0 0 10px;\n    padding: 0;\n  }\n  \n  .react-tabs__tab {\n    display: inline-block;\n    border: 1px solid transparent;\n    border-bottom: none;\n    bottom: -1px;\n    position: relative;\n    list-style: none;\n    padding: 6px 12px;\n    cursor: pointer;\n    color: #a0aec0;\n  }\n  \n  .react-tabs__tab--selected {\n    background: #4299e1;\n    border-color: #4a5568;\n    color: white;\n  }\n  \n  .react-tabs__tab:focus {\n    outline: none;\n  }\n  \n  .react-tabs__tab:hover {\n    background: #2d3748;\n  }\n  \n  .react-tabs__tab-panel {\n    display: none;\n  }\n  \n  .react-tabs__tab-panel--selected {\n    display: block;\n  }",""]),n.Z=r},4790:function(e,n,t){Promise.resolve().then(t.bind(t,122))},122:function(e,n,t){"use strict";t.r(n),t.d(n,{default:function(){return j}});var a=t(7437),s=t(2265),o=t(7818),r=t(2800),c=t(7022),l=t.n(c),i=t(3394),d=t.n(i),u=t(3514),p=t.n(u),b=t(4970),f=t.n(b),_=t(7793),h=t.n(_),g=t(7528),y=t.n(g),w=t(3683),m={};m.styleTagTransform=y(),m.setAttributes=f(),m.insert=p().bind(null,"head"),m.domAPI=d(),m.insertStyleElement=h(),l()(w.Z,m),w.Z&&w.Z.locals&&w.Z.locals;let v=(0,o.default)(()=>Promise.all([t.e(79),t.e(913)]).then(t.bind(t,9913)),{loadableGenerated:{webpack:()=>[9913]},ssr:!1}),x=(0,o.default)(()=>Promise.all([t.e(401),t.e(229),t.e(437)]).then(t.bind(t,8437)),{loadableGenerated:{webpack:()=>[8437]},ssr:!1}),k=(0,o.default)(()=>t.e(439).then(t.bind(t,2439)),{loadableGenerated:{webpack:()=>[2439]},ssr:!1});var j=()=>{let[e,n]=(0,s.useState)(null),[t,o]=(0,s.useState)(!0),[c,l]=(0,s.useState)(25),i=e=>{if("object"==typeof e&&null!==e)return e;try{let n=JSON.parse(e);if("object"==typeof n&&null!==n)return n}catch(e){console.error("Invalid JSON string provided, using empty object as fallback.",e)}return{}},d=(0,s.useCallback)(e=>{console.log("Received SSE message:",e),n(n=>{if(!n)return null;let t={...n};return"chat_history"===e.type?t.chat_history=e.chat_history:"plan"===e.type?t.current_plan=i(e.plan):"code"===e.type&&(t.step_codes=e.step_codes),console.log("Updated session data:",t),t})},[]);(0,s.useEffect)(()=>{(async()=>{try{let e=await (0,r.Gg)();console.log("Fetched session data:",e),n(e);let t=(0,r._I)(e.session_id);return t.onmessage=e=>{let n=JSON.parse(e.data);d(n)},t.onerror=e=>{console.error("EventSource failed:",e),t.close()},()=>{t.close()}}catch(e){console.error("Failed to fetch session data:",e)}finally{o(!1)}})()},[d]);let u=(0,s.useCallback)(async t=>{if(e){console.log("Updating plan with:",t);try{await (0,r.F9)(e.session_id,t),n(e=>{let n={...e,current_plan:t};return console.log("Updated session data after plan update:",n),n})}catch(e){console.error("Failed to update plan:",e)}}},[e]),p=(0,s.useCallback)(async(t,a)=>{if(e){console.log("Updating code for step ".concat(t,":"),a);try{let s={...e.step_codes,[t]:a};await (0,r.IX)(s),n(e=>{let n={...e,step_codes:s};return console.log("Updated session data after code update:",n),n})}catch(e){console.error("Failed to update code:",e)}}},[e]);return t?(0,a.jsx)("div",{className:"flex justify-center items-center h-screen bg-background text-foreground",children:"Loading..."}):e?(console.log("Rendering Home component with session data:",e),(0,a.jsxs)("div",{className:"flex h-screen w-full bg-background text-foreground overflow-hidden",children:[(0,a.jsx)("div",{style:{width:"".concat(c,"%")},className:"h-full overflow-hidden",children:(0,a.jsx)(v,{initialMessages:e.chat_history,currentPlan:e.current_plan})}),(0,a.jsx)(k,{onResize:e=>{l(e)}}),(0,a.jsx)("div",{style:{width:"".concat(100-c,"%")},className:"h-full overflow-hidden",children:(0,a.jsx)(x,{currentPlan:e.current_plan,stepCodes:e.step_codes,onPlanUpdate:u,onCodeUpdate:p})})]})):(0,a.jsx)("div",{className:"flex justify-center items-center h-screen bg-background text-foreground",children:"No session data available."})}},2800:function(e,n,t){"use strict";t.d(n,{F9:function(){return _},Gg:function(){return u},IX:function(){return h},MQ:function(){return d},_I:function(){return f},bE:function(){return p},cE:function(){return b},ef:function(){return g}});var a=t(8472),s=t(2649);let o="/api",r="session_id",c=e=>{s.Z.set(r,e,{expires:7})},l=()=>s.Z.get(r)||"",i=async()=>{let e=await a.Z.post("".concat(o,"/sessions"));return c(e.data.session_id),e.data},d=async()=>{let e=l();return e||c(e=(await i()).session_id),e},u=async()=>{let e=await d();return(await a.Z.get("".concat(o,"/sessions/").concat(e))).data},p=async e=>{let n=await d();return(await a.Z.post("".concat(o,"/schat"),{session_id:n,message:e})).data.session_id},b=e=>new EventSource("".concat(o,"/chat-stream?session_id=").concat(e)),f=e=>new EventSource("".concat(o,"/sse?session_id=").concat(e)),_=async(e,n)=>(await a.Z.put("".concat(o,"/sessions/").concat(e,"/current_plan"),n,{headers:{"Content-Type":"application/json"}})).data,h=async e=>{let n=await d();return(await a.Z.put("".concat(o,"/sessions/").concat(n,"/step_codes"),e)).data},g=async e=>{let n=await d();return(await a.Z.post("".concat(o,"/save_plan"),{session_id:n,plan:e})).data}}},function(e){e.O(0,[34,971,23,744],function(){return e(e.s=4790)}),_N_E=e.O()}]);