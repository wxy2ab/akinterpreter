"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[175],{78149:function(e,n,t){t.d(n,{M:function(){return r}});function r(e,n,{checkForDefaultPrevented:t=!0}={}){return function(r){if(e?.(r),!1===t||!r.defaultPrevented)return n?.(r)}}},90976:function(e,n,t){t.d(n,{B:function(){return s}});var r=t(2265),u=t(98324),i=t(1584),o=t(71538),l=t(57437);function s(e){let n=e+"CollectionProvider",[t,s]=(0,u.b)(n),[a,c]=t(n,{collectionRef:{current:null},itemMap:new Map}),d=e=>{let{scope:n,children:t}=e,u=r.useRef(null),i=r.useRef(new Map).current;return(0,l.jsx)(a,{scope:n,itemMap:i,collectionRef:u,children:t})};d.displayName=n;let f=e+"CollectionSlot",v=r.forwardRef((e,n)=>{let{scope:t,children:r}=e,u=c(f,t),s=(0,i.e)(n,u.collectionRef);return(0,l.jsx)(o.g7,{ref:s,children:r})});v.displayName=f;let m=e+"CollectionItemSlot",p="data-radix-collection-item",y=r.forwardRef((e,n)=>{let{scope:t,children:u,...s}=e,a=r.useRef(null),d=(0,i.e)(n,a),f=c(m,t);return r.useEffect(()=>(f.itemMap.set(a,{ref:a,...s}),()=>void f.itemMap.delete(a))),(0,l.jsx)(o.g7,{[p]:"",ref:d,children:u})});return y.displayName=m,[{Provider:d,Slot:v,ItemSlot:y},function(n){let t=c(e+"CollectionConsumer",n);return r.useCallback(()=>{let e=t.collectionRef.current;if(!e)return[];let n=Array.from(e.querySelectorAll("[".concat(p,"]")));return Array.from(t.itemMap.values()).sort((e,t)=>n.indexOf(e.ref.current)-n.indexOf(t.ref.current))},[t.collectionRef,t.itemMap])},s]}},1584:function(e,n,t){t.d(n,{F:function(){return u},e:function(){return i}});var r=t(2265);function u(...e){return n=>e.forEach(e=>{"function"==typeof e?e(n):null!=e&&(e.current=n)})}function i(...e){return r.useCallback(u(...e),e)}},98324:function(e,n,t){t.d(n,{b:function(){return i}});var r=t(2265),u=t(57437);function i(e,n=[]){let t=[],i=()=>{let n=t.map(e=>r.createContext(e));return function(t){let u=t?.[e]||n;return r.useMemo(()=>({[`__scope${e}`]:{...t,[e]:u}}),[t,u])}};return i.scopeName=e,[function(n,i){let o=r.createContext(i),l=t.length;function s(n){let{scope:t,children:i,...s}=n,a=t?.[e][l]||o,c=r.useMemo(()=>s,Object.values(s));return(0,u.jsx)(a.Provider,{value:c,children:i})}return t=[...t,i],s.displayName=n+"Provider",[s,function(t,u){let s=u?.[e][l]||o,a=r.useContext(s);if(a)return a;if(void 0!==i)return i;throw Error(`\`${t}\` must be used within \`${n}\``)}]},function(...e){let n=e[0];if(1===e.length)return n;let t=()=>{let t=e.map(e=>({useScope:e(),scopeName:e.scopeName}));return function(e){let u=t.reduce((n,{useScope:t,scopeName:r})=>{let u=t(e)[`__scope${r}`];return{...n,...u}},{});return r.useMemo(()=>({[`__scope${n.scopeName}`]:u}),[u])}};return t.scopeName=n.scopeName,t}(i,...n)]}},53938:function(e,n,t){t.d(n,{I0:function(){return E},XB:function(){return f},fC:function(){return y}});var r,u=t(2265),i=t(78149),o=t(25171),l=t(1584),s=t(75137),a=t(57437),c="dismissableLayer.update",d=u.createContext({layers:new Set,layersWithOutsidePointerEventsDisabled:new Set,branches:new Set}),f=u.forwardRef((e,n)=>{var t,f;let{disableOutsidePointerEvents:v=!1,onEscapeKeyDown:y,onPointerDownOutside:E,onFocusOutside:b,onInteractOutside:h,onDismiss:g,...N}=e,w=u.useContext(d),[C,O]=u.useState(null),R=null!==(f=null==C?void 0:C.ownerDocument)&&void 0!==f?f:null===(t=globalThis)||void 0===t?void 0:t.document,[,P]=u.useState({}),M=(0,l.e)(n,e=>O(e)),L=Array.from(w.layers),[W]=[...w.layersWithOutsidePointerEventsDisabled].slice(-1),j=L.indexOf(W),x=C?L.indexOf(C):-1,D=w.layersWithOutsidePointerEventsDisabled.size>0,S=x>=j,T=function(e){var n;let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null===(n=globalThis)||void 0===n?void 0:n.document,r=(0,s.W)(e),i=u.useRef(!1),o=u.useRef(()=>{});return u.useEffect(()=>{let e=e=>{if(e.target&&!i.current){let n=function(){p("dismissableLayer.pointerDownOutside",r,u,{discrete:!0})},u={originalEvent:e};"touch"===e.pointerType?(t.removeEventListener("click",o.current),o.current=n,t.addEventListener("click",o.current,{once:!0})):n()}else t.removeEventListener("click",o.current);i.current=!1},n=window.setTimeout(()=>{t.addEventListener("pointerdown",e)},0);return()=>{window.clearTimeout(n),t.removeEventListener("pointerdown",e),t.removeEventListener("click",o.current)}},[t,r]),{onPointerDownCapture:()=>i.current=!0}}(e=>{let n=e.target,t=[...w.branches].some(e=>e.contains(n));!S||t||(null==E||E(e),null==h||h(e),e.defaultPrevented||null==g||g())},R),A=function(e){var n;let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null===(n=globalThis)||void 0===n?void 0:n.document,r=(0,s.W)(e),i=u.useRef(!1);return u.useEffect(()=>{let e=e=>{e.target&&!i.current&&p("dismissableLayer.focusOutside",r,{originalEvent:e},{discrete:!1})};return t.addEventListener("focusin",e),()=>t.removeEventListener("focusin",e)},[t,r]),{onFocusCapture:()=>i.current=!0,onBlurCapture:()=>i.current=!1}}(e=>{let n=e.target;[...w.branches].some(e=>e.contains(n))||(null==b||b(e),null==h||h(e),e.defaultPrevented||null==g||g())},R);return!function(e,n=globalThis?.document){let t=(0,s.W)(e);u.useEffect(()=>{let e=e=>{"Escape"===e.key&&t(e)};return n.addEventListener("keydown",e,{capture:!0}),()=>n.removeEventListener("keydown",e,{capture:!0})},[t,n])}(e=>{x!==w.layers.size-1||(null==y||y(e),!e.defaultPrevented&&g&&(e.preventDefault(),g()))},R),u.useEffect(()=>{if(C)return v&&(0===w.layersWithOutsidePointerEventsDisabled.size&&(r=R.body.style.pointerEvents,R.body.style.pointerEvents="none"),w.layersWithOutsidePointerEventsDisabled.add(C)),w.layers.add(C),m(),()=>{v&&1===w.layersWithOutsidePointerEventsDisabled.size&&(R.body.style.pointerEvents=r)}},[C,R,v,w]),u.useEffect(()=>()=>{C&&(w.layers.delete(C),w.layersWithOutsidePointerEventsDisabled.delete(C),m())},[C,w]),u.useEffect(()=>{let e=()=>P({});return document.addEventListener(c,e),()=>document.removeEventListener(c,e)},[]),(0,a.jsx)(o.WV.div,{...N,ref:M,style:{pointerEvents:D?S?"auto":"none":void 0,...e.style},onFocusCapture:(0,i.M)(e.onFocusCapture,A.onFocusCapture),onBlurCapture:(0,i.M)(e.onBlurCapture,A.onBlurCapture),onPointerDownCapture:(0,i.M)(e.onPointerDownCapture,T.onPointerDownCapture)})});f.displayName="DismissableLayer";var v=u.forwardRef((e,n)=>{let t=u.useContext(d),r=u.useRef(null),i=(0,l.e)(n,r);return u.useEffect(()=>{let e=r.current;if(e)return t.branches.add(e),()=>{t.branches.delete(e)}},[t.branches]),(0,a.jsx)(o.WV.div,{...e,ref:i})});function m(){let e=new CustomEvent(c);document.dispatchEvent(e)}function p(e,n,t,r){let{discrete:u}=r,i=t.originalEvent.target,l=new CustomEvent(e,{bubbles:!1,cancelable:!0,detail:t});n&&i.addEventListener(e,n,{once:!0}),u?(0,o.jH)(i,l):i.dispatchEvent(l)}v.displayName="DismissableLayerBranch";var y=f,E=v},56935:function(e,n,t){t.d(n,{h:function(){return s}});var r=t(2265),u=t(54887),i=t(25171),o=t(1336),l=t(57437),s=r.forwardRef((e,n)=>{var t,s;let{container:a,...c}=e,[d,f]=r.useState(!1);(0,o.b)(()=>f(!0),[]);let v=a||d&&(null===(s=globalThis)||void 0===s?void 0:null===(t=s.document)||void 0===t?void 0:t.body);return v?u.createPortal((0,l.jsx)(i.WV.div,{...c,ref:n}),v):null});s.displayName="Portal"},31383:function(e,n,t){t.d(n,{z:function(){return l}});var r=t(2265),u=t(54887),i=t(1584),o=t(1336),l=e=>{var n,t;let l,a;let{present:c,children:d}=e,f=function(e){var n,t;let[i,l]=r.useState(),a=r.useRef({}),c=r.useRef(e),d=r.useRef("none"),[f,v]=(n=e?"mounted":"unmounted",t={mounted:{UNMOUNT:"unmounted",ANIMATION_OUT:"unmountSuspended"},unmountSuspended:{MOUNT:"mounted",ANIMATION_END:"unmounted"},unmounted:{MOUNT:"mounted"}},r.useReducer((e,n)=>{let r=t[e][n];return null!=r?r:e},n));return r.useEffect(()=>{let e=s(a.current);d.current="mounted"===f?e:"none"},[f]),(0,o.b)(()=>{let n=a.current,t=c.current;if(t!==e){let r=d.current,u=s(n);e?v("MOUNT"):"none"===u||(null==n?void 0:n.display)==="none"?v("UNMOUNT"):t&&r!==u?v("ANIMATION_OUT"):v("UNMOUNT"),c.current=e}},[e,v]),(0,o.b)(()=>{if(i){let e=e=>{let n=s(a.current).includes(e.animationName);e.target===i&&n&&u.flushSync(()=>v("ANIMATION_END"))},n=e=>{e.target===i&&(d.current=s(a.current))};return i.addEventListener("animationstart",n),i.addEventListener("animationcancel",e),i.addEventListener("animationend",e),()=>{i.removeEventListener("animationstart",n),i.removeEventListener("animationcancel",e),i.removeEventListener("animationend",e)}}v("ANIMATION_END")},[i,v]),{isPresent:["mounted","unmountSuspended"].includes(f),ref:r.useCallback(e=>{e&&(a.current=getComputedStyle(e)),l(e)},[])}}(c),v="function"==typeof d?d({present:f.isPresent}):r.Children.only(d),m=(0,i.e)(f.ref,(l=null===(n=Object.getOwnPropertyDescriptor(v.props,"ref"))||void 0===n?void 0:n.get)&&"isReactWarning"in l&&l.isReactWarning?v.ref:(l=null===(t=Object.getOwnPropertyDescriptor(v,"ref"))||void 0===t?void 0:t.get)&&"isReactWarning"in l&&l.isReactWarning?v.props.ref:v.props.ref||v.ref);return"function"==typeof d||f.isPresent?r.cloneElement(v,{ref:m}):null};function s(e){return(null==e?void 0:e.animationName)||"none"}l.displayName="Presence"},25171:function(e,n,t){t.d(n,{WV:function(){return l},jH:function(){return s}});var r=t(2265),u=t(54887),i=t(71538),o=t(57437),l=["a","button","div","form","h2","h3","img","input","label","li","nav","ol","p","span","svg","ul"].reduce((e,n)=>{let t=r.forwardRef((e,t)=>{let{asChild:r,...u}=e,l=r?i.g7:n;return"undefined"!=typeof window&&(window[Symbol.for("radix-ui")]=!0),(0,o.jsx)(l,{...u,ref:t})});return t.displayName=`Primitive.${n}`,{...e,[n]:t}},{});function s(e,n){e&&u.flushSync(()=>e.dispatchEvent(n))}},71538:function(e,n,t){t.d(n,{g7:function(){return o}});var r=t(2265),u=t(1584),i=t(57437),o=r.forwardRef((e,n)=>{let{children:t,...u}=e,o=r.Children.toArray(t),s=o.find(a);if(s){let e=s.props.children,t=o.map(n=>n!==s?n:r.Children.count(e)>1?r.Children.only(null):r.isValidElement(e)?e.props.children:null);return(0,i.jsx)(l,{...u,ref:n,children:r.isValidElement(e)?r.cloneElement(e,void 0,t):null})}return(0,i.jsx)(l,{...u,ref:n,children:t})});o.displayName="Slot";var l=r.forwardRef((e,n)=>{let{children:t,...i}=e;if(r.isValidElement(t)){let e,o;let l=(e=Object.getOwnPropertyDescriptor(t.props,"ref")?.get)&&"isReactWarning"in e&&e.isReactWarning?t.ref:(e=Object.getOwnPropertyDescriptor(t,"ref")?.get)&&"isReactWarning"in e&&e.isReactWarning?t.props.ref:t.props.ref||t.ref;return r.cloneElement(t,{...function(e,n){let t={...n};for(let r in n){let u=e[r],i=n[r];/^on[A-Z]/.test(r)?u&&i?t[r]=(...e)=>{i(...e),u(...e)}:u&&(t[r]=u):"style"===r?t[r]={...u,...i}:"className"===r&&(t[r]=[u,i].filter(Boolean).join(" "))}return{...e,...t}}(i,t.props),ref:n?(0,u.F)(n,l):l})}return r.Children.count(t)>1?r.Children.only(null):null});l.displayName="SlotClone";var s=({children:e})=>(0,i.jsx)(i.Fragment,{children:e});function a(e){return r.isValidElement(e)&&e.type===s}},75137:function(e,n,t){t.d(n,{W:function(){return u}});var r=t(2265);function u(e){let n=r.useRef(e);return r.useEffect(()=>{n.current=e}),r.useMemo(()=>(...e)=>n.current?.(...e),[])}},91715:function(e,n,t){t.d(n,{T:function(){return i}});var r=t(2265),u=t(75137);function i({prop:e,defaultProp:n,onChange:t=()=>{}}){let[i,o]=function({defaultProp:e,onChange:n}){let t=r.useState(e),[i]=t,o=r.useRef(i),l=(0,u.W)(n);return r.useEffect(()=>{o.current!==i&&(l(i),o.current=i)},[i,o,l]),t}({defaultProp:n,onChange:t}),l=void 0!==e,s=l?e:i,a=(0,u.W)(t);return[s,r.useCallback(n=>{if(l){let t="function"==typeof n?n(e):n;t!==e&&a(t)}else o(n)},[l,e,o,a])]}},1336:function(e,n,t){t.d(n,{b:function(){return u}});var r=t(2265),u=globalThis?.document?r.useLayoutEffect:()=>{}},12218:function(e,n,t){t.d(n,{j:function(){return i}});let r=e=>"boolean"==typeof e?"".concat(e):0===e?"0":e,u=function(){for(var e,n,t=0,r="";t<arguments.length;)(e=arguments[t++])&&(n=function e(n){var t,r,u="";if("string"==typeof n||"number"==typeof n)u+=n;else if("object"==typeof n){if(Array.isArray(n))for(t=0;t<n.length;t++)n[t]&&(r=e(n[t]))&&(u&&(u+=" "),u+=r);else for(t in n)n[t]&&(u&&(u+=" "),u+=t)}return u}(e))&&(r&&(r+=" "),r+=n);return r},i=(e,n)=>t=>{var i;if((null==n?void 0:n.variants)==null)return u(e,null==t?void 0:t.class,null==t?void 0:t.className);let{variants:o,defaultVariants:l}=n,s=Object.keys(o).map(e=>{let n=null==t?void 0:t[e],u=null==l?void 0:l[e];if(null===n)return null;let i=r(n)||r(u);return o[e][i]}),a=t&&Object.entries(t).reduce((e,n)=>{let[t,r]=n;return void 0===r||(e[t]=r),e},{});return u(e,s,null==n?void 0:null===(i=n.compoundVariants)||void 0===i?void 0:i.reduce((e,n)=>{let{class:t,className:r,...u}=n;return Object.entries(u).every(e=>{let[n,t]=e;return Array.isArray(t)?t.includes({...l,...a}[n]):({...l,...a})[n]===t})?[...e,t,r]:e},[]),null==t?void 0:t.class,null==t?void 0:t.className)}}}]);