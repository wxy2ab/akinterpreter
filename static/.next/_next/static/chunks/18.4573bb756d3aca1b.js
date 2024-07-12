(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[18],{8502:function(e,t,r){!function(e){"use strict";function t(e){return RegExp("^(("+e.join(")|(")+"))\\b")}var r=t(["and","or","not","is"]),o=["as","assert","break","class","continue","def","del","elif","else","except","finally","for","from","global","if","import","lambda","pass","raise","return","try","while","with","yield","in","False","True"],n=["abs","all","any","bin","bool","bytearray","callable","chr","classmethod","compile","complex","delattr","dict","dir","divmod","enumerate","eval","filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input","int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview","min","next","object","oct","open","ord","pow","property","range","repr","reversed","round","set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip","__import__","NotImplemented","Ellipsis","__debug__"];function i(e){return e.scopes[e.scopes.length-1]}e.registerHelper("hintWords","python",o.concat(n).concat(["exec","print"])),e.defineMode("python",function(s,a){for(var c="error",l=a.delimiters||a.singleDelimiters||/^[\(\)\[\]\{\}@,:`=;\.\\]/,u=[a.singleOperators,a.doubleOperators,a.doubleDelimiters,a.tripleDelimiters,a.operators||/^([-+*/%\/&|^]=?|[<>=]+|\/\/=?|\*\*=?|!=|[~!@]|\.\.\.)/],d=0;d<u.length;d++)u[d]||u.splice(d--,1);var p=a.hangingIndent||s.indentUnit,f=o,h=n;void 0!=a.extra_keywords&&(f=f.concat(a.extra_keywords)),void 0!=a.extra_builtins&&(h=h.concat(a.extra_builtins));var g=!(a.version&&3>Number(a.version));if(g){var y=a.identifiers||/^[_A-Za-z\u00A1-\uFFFF][_A-Za-z0-9\u00A1-\uFFFF]*/;f=f.concat(["nonlocal","None","aiter","anext","async","await","breakpoint","match","case"]),h=h.concat(["ascii","bytes","exec","print"]);var m=RegExp("^(([rbuf]|(br)|(rb)|(fr)|(rf))?('{3}|\"{3}|['\"]))","i")}else{var y=a.identifiers||/^[_A-Za-z][_A-Za-z0-9]*/;f=f.concat(["exec","print"]),h=h.concat(["apply","basestring","buffer","cmp","coerce","execfile","file","intern","long","raw_input","reduce","reload","unichr","unicode","xrange","None"]);var m=RegExp("^(([rubf]|(ur)|(br))?('{3}|\"{3}|['\"]))","i")}var b=t(f),v=t(h);function C(e,t){var r=e.sol()&&"\\"!=t.lastToken;if(r&&(t.indent=e.indentation()),r&&"py"==i(t).type){var o=i(t).offset;if(e.eatSpace()){var n=e.indentation();return n>o?D(t):n<o&&x(e,t)&&"#"!=e.peek()&&(t.errorToken=!0),null}var s=k(e,t);return o>0&&x(e,t)&&(s+=" "+c),s}return k(e,t)}function k(e,t,o){if(e.eatSpace())return null;if(!o&&e.match(/^#.*/))return"comment";if(e.match(/^[0-9\.]/,!1)){var n=!1;if(e.match(/^[\d_]*\.\d+(e[\+\-]?\d+)?/i)&&(n=!0),e.match(/^[\d_]+\.\d*/)&&(n=!0),e.match(/^\.\d+/)&&(n=!0),n)return e.eat(/J/i),"number";var i=!1;if(e.match(/^0x[0-9a-f_]+/i)&&(i=!0),e.match(/^0b[01_]+/i)&&(i=!0),e.match(/^0o[0-7_]+/i)&&(i=!0),e.match(/^[1-9][\d_]*(e[\+\-]?[\d_]+)?/)&&(e.eat(/J/i),i=!0),e.match(/^0(?![\dx])/i)&&(i=!0),i)return e.eat(/L/i),"number"}if(e.match(m))return -1!==e.current().toLowerCase().indexOf("f")?t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var r=1==e.length,o="string";function n(i,s){for(;!i.eol();)if(i.eatWhile(/[^'"\{\}\\]/),i.eat("\\")){if(i.next(),r&&i.eol())return o}else if(i.match(e))return s.tokenize=t,o;else if(i.match("{{"))return o;else if(i.match("{",!1)){if(s.tokenize=function e(t){return function(r,o){var i=k(r,o,!0);return"punctuation"==i&&("{"==r.current()?o.tokenize=e(t+1):"}"==r.current()&&(t>1?o.tokenize=e(t-1):o.tokenize=n)),i}}(0),i.current())return o;return s.tokenize(i,s)}else{if(i.match("}}"))return o;if(i.match("}"))return c;i.eat(/['"]/)}if(r){if(a.singleLineStringErrors)return c;s.tokenize=t}return o}return n.isString=!0,n}(e.current(),t.tokenize):t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var r=1==e.length,o="string";function n(n,i){for(;!n.eol();)if(n.eatWhile(/[^'"\\]/),n.eat("\\")){if(n.next(),r&&n.eol())return o}else{if(n.match(e))return i.tokenize=t,o;n.eat(/['"]/)}if(r){if(a.singleLineStringErrors)return c;i.tokenize=t}return o}return n.isString=!0,n}(e.current(),t.tokenize),t.tokenize(e,t);for(var s=0;s<u.length;s++)if(e.match(u[s]))return"operator";return e.match(l)?"punctuation":"."==t.lastToken&&e.match(y)?"property":e.match(b)||e.match(r)?"keyword":e.match(v)?"builtin":e.match(/^(self|cls)\b/)?"variable-2":e.match(y)?"def"==t.lastToken||"class"==t.lastToken?"def":"variable":(e.next(),o?null:c)}function D(e){for(;"py"!=i(e).type;)e.scopes.pop();e.scopes.push({offset:i(e).offset+s.indentUnit,type:"py",align:null})}function x(e,t){for(var r=e.indentation();t.scopes.length>1&&i(t).offset>r;){if("py"!=i(t).type)return!0;t.scopes.pop()}return i(t).offset!=r}return{startState:function(e){return{tokenize:C,scopes:[{offset:e||0,type:"py",align:null}],indent:e||0,lastToken:null,lambda:!1,dedent:0}},token:function(e,t){var r=t.errorToken;r&&(t.errorToken=!1);var o=function(e,t){e.sol()&&(t.beginningOfLine=!0,t.dedent=!1);var r=t.tokenize(e,t),o=e.current();if(t.beginningOfLine&&"@"==o)return e.match(y,!1)?"meta":g?"operator":c;if(/\S/.test(o)&&(t.beginningOfLine=!1),("variable"==r||"builtin"==r)&&"meta"==t.lastToken&&(r="meta"),("pass"==o||"return"==o)&&(t.dedent=!0),"lambda"==o&&(t.lambda=!0),":"==o&&!t.lambda&&"py"==i(t).type&&e.match(/^\s*(?:#|$)/,!1)&&D(t),1==o.length&&!/string|comment/.test(r)){var n="[({".indexOf(o);if(-1!=n&&function(e,t,r){var o=e.match(/^[\s\[\{\(]*(?:#|$)/,!1)?null:e.column()+1;t.scopes.push({offset:t.indent+p,type:r,align:o})}(e,t,"])}".slice(n,n+1)),-1!=(n="])}".indexOf(o))){if(i(t).type!=o)return c;t.indent=t.scopes.pop().offset-p}}return t.dedent&&e.eol()&&"py"==i(t).type&&t.scopes.length>1&&t.scopes.pop(),r}(e,t);return o&&"comment"!=o&&(t.lastToken="keyword"==o||"punctuation"==o?e.current():o),"punctuation"==o&&(o=null),e.eol()&&t.lambda&&(t.lambda=!1),r?o+" "+c:o},indent:function(t,r){if(t.tokenize!=C)return t.tokenize.isString?e.Pass:0;var o=i(t),n=o.type==r.charAt(0)||"py"==o.type&&!t.dedent&&/^(else:|elif |except |finally:)/.test(r);return null!=o.align?o.align-(n?1:0):o.offset-(n?p:0)},electricInput:/^\s*([\}\]\)]|else:|elif |except |finally:)$/,closeBrackets:{triples:"'\""},lineComment:"#",fold:"indent"}}),e.defineMIME("text/x-python","python"),e.defineMIME("text/x-cython",{name:"python",extra_keywords:"by cdef cimport cpdef ctypedef enum except extern gil include nogil property public readonly struct union DEF IF ELIF ELSE".split(" ")})}(r(3837))},8484:function(e,t,r){"use strict";function o(){return(o=Object.assign?Object.assign.bind():function(e){for(var t=1;t<arguments.length;t++){var r=arguments[t];for(var o in r)Object.prototype.hasOwnProperty.call(r,o)&&(e[o]=r[o])}return e}).apply(this,arguments)}function n(e){return(n="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}var i,s,a=(i=function(e,t){return(i=Object.setPrototypeOf||({__proto__:[]})instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var r in t)Object.prototype.hasOwnProperty.call(t,r)&&(e[r]=t[r])})(e,t)},function(e,t){if("function"!=typeof t&&null!==t)throw TypeError("Class extends value "+String(t)+" is not a constructor or null");function r(){this.constructor=e}i(e,t),e.prototype=null===t?Object.create(t):(r.prototype=t.prototype,new r)});t.fk=void 0;var c=r(2265),l="undefined"==typeof navigator||void 0!==r.g&&!0===r.g.PREVENT_CODEMIRROR_RENDER;l||(s=r(3837));var u=function(){function e(){}return e.equals=function(e,t){var r=this,o=Object.keys,i=n(e),s=n(t);return e&&t&&"object"===i&&i===s?o(e).length===o(t).length&&o(e).every(function(o){return r.equals(e[o],t[o])}):e===t},e}(),d=function(){function e(e,t){this.editor=e,this.props=t}return e.prototype.delegateCursor=function(e,t,r){var o=this.editor.getDoc();r&&this.editor.focus(),t?o.setCursor(e):o.setCursor(e,null,{scroll:!1})},e.prototype.delegateScroll=function(e){this.editor.scrollTo(e.x,e.y)},e.prototype.delegateSelection=function(e,t){this.editor.getDoc().setSelections(e),t&&this.editor.focus()},e.prototype.apply=function(e){e&&e.selection&&e.selection.ranges&&this.delegateSelection(e.selection.ranges,e.selection.focus||!1),e&&e.cursor&&this.delegateCursor(e.cursor,e.autoScroll||!1,this.editor.getOption("autofocus")||!1),e&&e.scroll&&this.delegateScroll(e.scroll)},e.prototype.applyNext=function(e,t,r){e&&e.selection&&e.selection.ranges&&t&&t.selection&&t.selection.ranges&&!u.equals(e.selection.ranges,t.selection.ranges)&&this.delegateSelection(t.selection.ranges,t.selection.focus||!1),e&&e.cursor&&t&&t.cursor&&!u.equals(e.cursor,t.cursor)&&this.delegateCursor(r.cursor||t.cursor,t.autoScroll||!1,t.autoCursor||!1),e&&e.scroll&&t&&t.scroll&&!u.equals(e.scroll,t.scroll)&&this.delegateScroll(t.scroll)},e.prototype.applyUserDefined=function(e,t){t&&t.cursor&&this.delegateCursor(t.cursor,e.autoScroll||!1,this.editor.getOption("autofocus")||!1)},e.prototype.wire=function(e){var t=this;Object.keys(e||{}).filter(function(e){return/^on/.test(e)}).forEach(function(e){switch(e){case"onBlur":t.editor.on("blur",function(e,r){t.props.onBlur(t.editor,r)});break;case"onContextMenu":t.editor.on("contextmenu",function(e,r){t.props.onContextMenu(t.editor,r)});break;case"onCopy":t.editor.on("copy",function(e,r){t.props.onCopy(t.editor,r)});break;case"onCursor":t.editor.on("cursorActivity",function(e){t.props.onCursor(t.editor,t.editor.getDoc().getCursor())});break;case"onCursorActivity":t.editor.on("cursorActivity",function(e){t.props.onCursorActivity(t.editor)});break;case"onCut":t.editor.on("cut",function(e,r){t.props.onCut(t.editor,r)});break;case"onDblClick":t.editor.on("dblclick",function(e,r){t.props.onDblClick(t.editor,r)});break;case"onDragEnter":t.editor.on("dragenter",function(e,r){t.props.onDragEnter(t.editor,r)});break;case"onDragLeave":t.editor.on("dragleave",function(e,r){t.props.onDragLeave(t.editor,r)});break;case"onDragOver":t.editor.on("dragover",function(e,r){t.props.onDragOver(t.editor,r)});break;case"onDragStart":t.editor.on("dragstart",function(e,r){t.props.onDragStart(t.editor,r)});break;case"onDrop":t.editor.on("drop",function(e,r){t.props.onDrop(t.editor,r)});break;case"onFocus":t.editor.on("focus",function(e,r){t.props.onFocus(t.editor,r)});break;case"onGutterClick":t.editor.on("gutterClick",function(e,r,o,n){t.props.onGutterClick(t.editor,r,o,n)});break;case"onInputRead":t.editor.on("inputRead",function(e,r){t.props.onInputRead(t.editor,r)});break;case"onKeyDown":t.editor.on("keydown",function(e,r){t.props.onKeyDown(t.editor,r)});break;case"onKeyHandled":t.editor.on("keyHandled",function(e,r,o){t.props.onKeyHandled(t.editor,r,o)});break;case"onKeyPress":t.editor.on("keypress",function(e,r){t.props.onKeyPress(t.editor,r)});break;case"onKeyUp":t.editor.on("keyup",function(e,r){t.props.onKeyUp(t.editor,r)});break;case"onMouseDown":t.editor.on("mousedown",function(e,r){t.props.onMouseDown(t.editor,r)});break;case"onPaste":t.editor.on("paste",function(e,r){t.props.onPaste(t.editor,r)});break;case"onRenderLine":t.editor.on("renderLine",function(e,r,o){t.props.onRenderLine(t.editor,r,o)});break;case"onScroll":t.editor.on("scroll",function(e){t.props.onScroll(t.editor,t.editor.getScrollInfo())});break;case"onSelection":t.editor.on("beforeSelectionChange",function(e,r){t.props.onSelection(t.editor,r)});break;case"onTouchStart":t.editor.on("touchstart",function(e,r){t.props.onTouchStart(t.editor,r)});break;case"onUpdate":t.editor.on("update",function(e){t.props.onUpdate(t.editor)});break;case"onViewportChange":t.editor.on("viewportChange",function(e,r,o){t.props.onViewportChange(t.editor,r,o)})}})},e}(),p=function(e){function t(t){var r=e.call(this,t)||this;return l||(r.applied=!1,r.appliedNext=!1,r.appliedUserDefined=!1,r.deferred=null,r.emulating=!1,r.hydrated=!1,r.initCb=function(){r.props.editorDidConfigure&&r.props.editorDidConfigure(r.editor)},r.mounted=!1),r}return a(t,e),t.prototype.hydrate=function(e){var t=this,r=e&&e.options?e.options:{},n=o({},s.defaults,this.editor.options,r);Object.keys(n).some(function(e){return t.editor.getOption(e)!==n[e]})&&Object.keys(n).forEach(function(e){r.hasOwnProperty(e)&&t.editor.getOption(e)!==n[e]&&(t.editor.setOption(e,n[e]),t.mirror.setOption(e,n[e]))}),this.hydrated||(this.deferred?this.resolveChange(e.value):this.initChange(e.value||"")),this.hydrated=!0},t.prototype.initChange=function(e){this.emulating=!0;var t=this.editor.getDoc(),r=t.lastLine(),o=t.getLine(t.lastLine()).length;t.replaceRange(e||"",{line:0,ch:0},{line:r,ch:o}),this.mirror.setValue(e),t.clearHistory(),this.mirror.clearHistory(),this.emulating=!1},t.prototype.resolveChange=function(e){this.emulating=!0;var t=this.editor.getDoc();if("undo"===this.deferred.origin?t.undo():"redo"===this.deferred.origin?t.redo():t.replaceRange(this.deferred.text,this.deferred.from,this.deferred.to,this.deferred.origin),e&&e!==t.getValue()){var r=t.getCursor();t.setValue(e),t.setCursor(r)}this.emulating=!1,this.deferred=null},t.prototype.mirrorChange=function(e){var t=this.editor.getDoc();return"undo"===e.origin?(t.setHistory(this.mirror.getHistory()),this.mirror.undo()):"redo"===e.origin?(t.setHistory(this.mirror.getHistory()),this.mirror.redo()):this.mirror.replaceRange(e.text,e.from,e.to,e.origin),this.mirror.getValue()},t.prototype.componentDidMount=function(){var e=this;!l&&(this.props.defineMode&&this.props.defineMode.name&&this.props.defineMode.fn&&s.defineMode(this.props.defineMode.name,this.props.defineMode.fn),this.editor=s(this.ref,this.props.options),this.shared=new d(this.editor,this.props),this.mirror=s(function(){},this.props.options),this.editor.on("electricInput",function(){e.mirror.setHistory(e.editor.getDoc().getHistory())}),this.editor.on("cursorActivity",function(){e.mirror.setCursor(e.editor.getDoc().getCursor())}),this.editor.on("beforeChange",function(t,r){if(!e.emulating){r.cancel(),e.deferred=r;var o=e.mirrorChange(e.deferred);e.props.onBeforeChange&&e.props.onBeforeChange(e.editor,e.deferred,o)}}),this.editor.on("change",function(t,r){e.mounted&&e.props.onChange&&e.props.onChange(e.editor,r,e.editor.getValue())}),this.hydrate(this.props),this.shared.apply(this.props),this.applied=!0,this.mounted=!0,this.shared.wire(this.props),this.editor.getOption("autofocus")&&this.editor.focus(),this.props.editorDidMount&&this.props.editorDidMount(this.editor,this.editor.getValue(),this.initCb))},t.prototype.componentDidUpdate=function(e){if(!l){var t={cursor:null};this.props.value!==e.value&&(this.hydrated=!1),this.props.autoCursor||void 0===this.props.autoCursor||(t.cursor=this.editor.getDoc().getCursor()),this.hydrate(this.props),this.appliedNext||(this.shared.applyNext(e,this.props,t),this.appliedNext=!0),this.shared.applyUserDefined(e,t),this.appliedUserDefined=!0}},t.prototype.componentWillUnmount=function(){!l&&this.props.editorWillUnmount&&this.props.editorWillUnmount(s)},t.prototype.shouldComponentUpdate=function(e,t){return!l},t.prototype.render=function(){var e=this;if(l)return null;var t=this.props.className?"react-codemirror2 ".concat(this.props.className):"react-codemirror2";return c.createElement("div",{className:t,ref:function(t){return e.ref=t}})},t}(c.Component);t.fk=p,function(e){function t(t){var r=e.call(this,t)||this;return l||(r.applied=!1,r.appliedUserDefined=!1,r.continueChange=!1,r.detached=!1,r.hydrated=!1,r.initCb=function(){r.props.editorDidConfigure&&r.props.editorDidConfigure(r.editor)},r.mounted=!1,r.onBeforeChangeCb=function(){r.continueChange=!0}),r}a(t,e),t.prototype.hydrate=function(e){var t=this,r=e&&e.options?e.options:{},n=o({},s.defaults,this.editor.options,r);if(Object.keys(n).some(function(e){return t.editor.getOption(e)!==n[e]})&&Object.keys(n).forEach(function(e){r.hasOwnProperty(e)&&t.editor.getOption(e)!==n[e]&&t.editor.setOption(e,n[e])}),!this.hydrated){var i=this.editor.getDoc(),a=i.lastLine(),c=i.getLine(i.lastLine()).length;i.replaceRange(e.value||"",{line:0,ch:0},{line:a,ch:c})}this.hydrated=!0},t.prototype.componentDidMount=function(){var e=this;!l&&(this.detached=!0===this.props.detach,this.props.defineMode&&this.props.defineMode.name&&this.props.defineMode.fn&&s.defineMode(this.props.defineMode.name,this.props.defineMode.fn),this.editor=s(this.ref,this.props.options),this.shared=new d(this.editor,this.props),this.editor.on("beforeChange",function(t,r){e.props.onBeforeChange&&e.props.onBeforeChange(e.editor,r,e.editor.getValue(),e.onBeforeChangeCb)}),this.editor.on("change",function(t,r){e.mounted&&e.props.onChange&&(e.props.onBeforeChange?e.continueChange&&e.props.onChange(e.editor,r,e.editor.getValue()):e.props.onChange(e.editor,r,e.editor.getValue()))}),this.hydrate(this.props),this.shared.apply(this.props),this.applied=!0,this.mounted=!0,this.shared.wire(this.props),this.editor.getDoc().clearHistory(),this.props.editorDidMount&&this.props.editorDidMount(this.editor,this.editor.getValue(),this.initCb))},t.prototype.componentDidUpdate=function(e){if(this.detached&&!1===this.props.detach&&(this.detached=!1,e.editorDidAttach&&e.editorDidAttach(this.editor)),!this.detached&&!0===this.props.detach&&(this.detached=!0,e.editorDidDetach&&e.editorDidDetach(this.editor)),!l&&!this.detached){var t={cursor:null};this.props.value!==e.value&&(this.hydrated=!1,this.applied=!1,this.appliedUserDefined=!1),e.autoCursor||void 0===e.autoCursor||(t.cursor=this.editor.getDoc().getCursor()),this.hydrate(this.props),this.applied||(this.shared.apply(e),this.applied=!0),this.appliedUserDefined||(this.shared.applyUserDefined(e,t),this.appliedUserDefined=!0)}},t.prototype.componentWillUnmount=function(){!l&&this.props.editorWillUnmount&&this.props.editorWillUnmount(s)},t.prototype.shouldComponentUpdate=function(e,t){var r=!0;return l&&(r=!1),this.detached&&e.detach&&(r=!1),r},t.prototype.render=function(){var e=this;if(l)return null;var t=this.props.className?"react-codemirror2 ".concat(this.props.className):"react-codemirror2";return c.createElement("div",{className:t,ref:function(t){return e.ref=t}})}}(c.Component)},4749:function(e,t,r){"use strict";let o;r.d(t,{OK:function(){return S},td:function(){return w},x4:function(){return M},mQ:function(){return k}});var n=r(2265);function i(e){return t=>!!t.type&&t.type.tabsRole===e}let s=i("Tab"),a=i("TabList"),c=i("TabPanel");function l(e,t){return n.Children.map(e,e=>null===e?null:s(e)||a(e)||c(e)?t(e):e.props&&e.props.children&&"object"==typeof e.props.children?(0,n.cloneElement)(e,{...e.props,children:l(e.props.children,t)}):e)}var u=function(){for(var e,t,r=0,o="",n=arguments.length;r<n;r++)(e=arguments[r])&&(t=function e(t){var r,o,n="";if("string"==typeof t||"number"==typeof t)n+=t;else if("object"==typeof t){if(Array.isArray(t)){var i=t.length;for(r=0;r<i;r++)t[r]&&(o=e(t[r]))&&(n&&(n+=" "),n+=o)}else for(o in t)t[o]&&(n&&(n+=" "),n+=o)}return n}(e))&&(o&&(o+=" "),o+=t);return o};function d(e){let t=0;return!function e(t,r){return n.Children.forEach(t,t=>{null!==t&&(s(t)||c(t)?r(t):t.props&&t.props.children&&"object"==typeof t.props.children&&(a(t)&&r(t),e(t.props.children,r)))})}(e,e=>{s(e)&&t++}),t}function p(e){return e&&"getAttribute"in e}function f(e){return p(e)&&e.getAttribute("data-rttab")}function h(e){return p(e)&&"true"===e.getAttribute("aria-disabled")}let g={className:"react-tabs",focus:!1},y=e=>{let t=(0,n.useRef)([]),r=(0,n.useRef)([]),i=(0,n.useRef)();function p(t,r){if(t<0||t>=b())return;let{onSelect:o,selectedIndex:n}=e;o(t,n,r)}function y(e){let t=b();for(let r=e+1;r<t;r++)if(!h(v(r)))return r;for(let t=0;t<e;t++)if(!h(v(t)))return t;return e}function m(e){let t=e;for(;t--;)if(!h(v(t)))return t;for(t=b();t-- >e;)if(!h(v(t)))return t;return e}function b(){let{children:t}=e;return d(t)}function v(e){return t.current[`tabs-${e}`]}function C(e){let t=e.target;do if(k(t)){if(h(t))return;p([].slice.call(t.parentNode.children).filter(f).indexOf(t),e);return}while(null!=(t=t.parentNode))}function k(e){if(!f(e))return!1;let t=e.parentElement;do{if(t===i.current)return!0;if(t.getAttribute("data-rttabs"))break;t=t.parentElement}while(t);return!1}let{children:D,className:x,disabledTabClassName:w,domRef:O,focus:E,forceRenderTabPanel:_,onSelect:S,selectedIndex:N,selectedTabClassName:R,selectedTabPanelClassName:T,environment:M,disableUpDownKeys:A,disableLeftRightKeys:U,...L}={...g,...e};return n.createElement("div",Object.assign({},L,{className:u(x),onClick:C,onKeyDown:function(t){let{direction:r,disableUpDownKeys:o,disableLeftRightKeys:n}=e;if(k(t.target)){let{selectedIndex:i}=e,s=!1,a=!1;("Space"===t.code||32===t.keyCode||"Enter"===t.code||13===t.keyCode)&&(s=!0,a=!1,C(t)),(n||37!==t.keyCode&&"ArrowLeft"!==t.code)&&(o||38!==t.keyCode&&"ArrowUp"!==t.code)?(n||39!==t.keyCode&&"ArrowRight"!==t.code)&&(o||40!==t.keyCode&&"ArrowDown"!==t.code)?35===t.keyCode||"End"===t.code?(i=function(){let e=b();for(;e--;)if(!h(v(e)))return e;return null}(),s=!0,a=!0):(36===t.keyCode||"Home"===t.code)&&(i=function(){let e=b();for(let t=0;t<e;t++)if(!h(v(t)))return t;return null}(),s=!0,a=!0):(i="rtl"===r?m(i):y(i),s=!0,a=!0):(i="rtl"===r?y(i):m(i),s=!0,a=!0),s&&t.preventDefault(),a&&p(i,t)}},ref:e=>{i.current=e,O&&O(e)},"data-rttabs":!0}),function(){let i=0,{children:u,disabledTabClassName:d,focus:p,forceRenderTabPanel:f,selectedIndex:h,selectedTabClassName:g,selectedTabPanelClassName:y,environment:m}=e;r.current=r.current||[];let C=r.current.length-b(),k=(0,n.useId)();for(;C++<0;)r.current.push(`${k}${r.current.length}`);return l(u,e=>{let u=e;if(a(e)){let i=0,a=!1;null==o&&function(e){let t=e||("undefined"!=typeof window?window:void 0);try{o=!!(void 0!==t&&t.document&&t.document.activeElement)}catch(e){o=!1}}(m);let c=m||("undefined"!=typeof window?window:void 0);o&&c&&(a=n.Children.toArray(e.props.children).filter(s).some((e,t)=>c.document.activeElement===v(t))),u=(0,n.cloneElement)(e,{children:l(e.props.children,e=>{let o=`tabs-${i}`,s=h===i,c={tabRef:e=>{t.current[o]=e},id:r.current[i],selected:s,focus:s&&(p||a)};return g&&(c.selectedClassName=g),d&&(c.disabledClassName=d),i++,(0,n.cloneElement)(e,c)})})}else if(c(e)){let t={id:r.current[i],selected:h===i};f&&(t.forceRender=f),y&&(t.selectedClassName=y),i++,u=(0,n.cloneElement)(e,t)}return u})}())};y.propTypes={};let m={defaultFocus:!1,focusTabOnClick:!0,forceRenderTabPanel:!1,selectedIndex:null,defaultIndex:null,environment:null,disableUpDownKeys:!1,disableLeftRightKeys:!1},b=e=>null===e.selectedIndex?1:0,v=(e,t)=>{},C=e=>{let{children:t,defaultFocus:r,defaultIndex:o,focusTabOnClick:i,onSelect:s,...a}={...m,...e},[c,l]=(0,n.useState)(r),[u]=(0,n.useState)(b(a)),[p,f]=(0,n.useState)(1===u?o||0:null);if((0,n.useEffect)(()=>{l(!1)},[]),1===u){let e=d(t);(0,n.useEffect)(()=>{null!=p&&f(Math.min(p,Math.max(0,e-1)))},[e])}v(a,u);let h={...e,...a};return h.focus=c,h.onSelect=(e,t,r)=>{("function"!=typeof s||!1!==s(e,t,r))&&(i&&l(!0),1===u&&f(e))},null!=p&&(h.selectedIndex=p),delete h.defaultFocus,delete h.defaultIndex,delete h.focusTabOnClick,n.createElement(y,h,t)};C.propTypes={},C.tabsRole="Tabs";var k=C;let D={className:"react-tabs__tab-list"},x=e=>{let{children:t,className:r,...o}={...D,...e};return n.createElement("ul",Object.assign({},o,{className:u(r),role:"tablist"}),t)};x.tabsRole="TabList",x.propTypes={};var w=x;let O="react-tabs__tab",E={className:O,disabledClassName:`${O}--disabled`,focus:!1,id:null,selected:!1,selectedClassName:`${O}--selected`},_=e=>{let t=(0,n.useRef)(),{children:r,className:o,disabled:i,disabledClassName:s,focus:a,id:c,selected:l,selectedClassName:d,tabIndex:p,tabRef:f,...h}={...E,...e};return(0,n.useEffect)(()=>{l&&a&&t.current.focus()},[l,a]),n.createElement("li",Object.assign({},h,{className:u(o,{[d]:l,[s]:i}),ref:e=>{t.current=e,f&&f(e)},role:"tab",id:`tab${c}`,"aria-selected":l?"true":"false","aria-disabled":i?"true":"false","aria-controls":`panel${c}`,tabIndex:p||(l?"0":null),"data-rttab":!0}),r)};_.propTypes={},_.tabsRole="Tab";var S=_;let N="react-tabs__tab-panel",R={className:N,forceRender:!1,selectedClassName:`${N}--selected`},T=e=>{let{children:t,className:r,forceRender:o,id:i,selected:s,selectedClassName:a,...c}={...R,...e};return n.createElement("div",Object.assign({},c,{className:u(r,{[a]:s}),role:"tabpanel",id:`panel${i}`,"aria-labelledby":`tab${i}`}),o||s?t:null)};T.tabsRole="TabPanel",T.propTypes={};var M=T},9877:function(){},2024:function(){},4943:function(){}}]);