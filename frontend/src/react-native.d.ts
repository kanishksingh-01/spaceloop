declare module 'react-native' {
  export interface ViewProps {
    className?: string;
    style?: any;
    children?: any;
    [key: string]: any;
  }
  export const View: any;

  export interface TextProps {
    className?: string;
    style?: any;
    numberOfLines?: number;
    children?: any;
    [key: string]: any;
  }
  export const Text: any;

  export interface PressableProps {
    className?: string;
    style?: any;
    onPress?: (event?: any) => void;
    disabled?: boolean;
    children?: any;
    [key: string]: any;
  }
  export const Pressable: any;

  export interface ScrollViewProps {
    className?: string;
    style?: any;
    ref?: any;
    children?: any;
    [key: string]: any;
  }
  export const ScrollView: any;

  export interface TextInputProps {
    className?: string;
    style?: any;
    value?: string;
    onChangeText?: (text: string) => void;
    onSubmitEditing?: () => void;
    placeholder?: string;
    placeholderTextColor?: string;
    secureTextEntry?: boolean;
    multiline?: boolean;
    numberOfLines?: number;
    keyboardType?: string;
    [key: string]: any;
  }
  export const TextInput: any;

  export interface ImageProps {
    className?: string;
    style?: any;
    source?: { uri?: string } | number;
    [key: string]: any;
  }
  export const Image: any;

  export const StyleSheet: {
    create: <T extends Record<string, any>>(styles: T) => T;
  };

  export const Platform: {
    OS: 'web' | 'ios' | 'android';
    select: <T>(specifics: { web?: T; default?: T }) => T;
  };
}

declare module 'react-native-web' {
  export const View: any;
  export const Text: any;
  export const Pressable: any;
  export const ScrollView: any;
  export const TextInput: any;
  export const Image: any;
  export const StyleSheet: any;
  export const Platform: any;
}
