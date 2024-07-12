// src/types/react-json-editor-ajrm.d.ts
declare module 'react-json-editor-ajrm' {
    import * as React from 'react';

    interface JSONInputProps {
        id: string;
        placeholder?: any;
        theme?: string;
        locale?: any;
        height?: string;
        width?: string;
        colors?: any;
        style?: any;
        viewOnly?: boolean;
        onChange?: (edit: any) => void;
        confirmGood?: boolean;
    }

    export default class JSONInput extends React.Component<JSONInputProps> {}
}

declare module 'react-json-editor-ajrm/locale/en' {
    const locale: any;
    export { locale };
}
