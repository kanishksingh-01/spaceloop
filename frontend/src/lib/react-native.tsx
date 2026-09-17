import React from 'react';

// Clean React Native Web primitives that seamlessly honor all Tailwind CSS layout & styling classes
export const View = React.forwardRef<HTMLDivElement, any>(
  ({ className = '', style, children, ...props }, ref) => {
    let extra = '';
    // If component specifies flexbox direction/alignment without explicit display class
    if (
      (className.includes('flex-row') ||
        className.includes('flex-col') ||
        className.includes('items-center') ||
        className.includes('justify-between')) &&
      !className.includes('flex') &&
      !className.includes('grid') &&
      !className.includes('hidden') &&
      !className.includes('inline')
    ) {
      extra = 'flex ';
    }
    return (
      <div
        ref={ref}
        className={`${extra}${className}`.trim()}
        style={style}
        {...props}
      >
        {children}
      </div>
    );
  }
);
View.displayName = 'View';

export const Text = React.forwardRef<HTMLSpanElement, any>(
  ({ className = '', style, numberOfLines, children, ...props }, ref) => {
    const lineClamp = numberOfLines ? `line-clamp-${numberOfLines}` : '';
    return (
      <span
        ref={ref}
        className={`${lineClamp} ${className}`}
        style={style}
        {...props}
      >
        {children}
      </span>
    );
  }
);
Text.displayName = 'Text';

export const Pressable = React.forwardRef<HTMLButtonElement, any>(
  ({ className = '', style, onPress, onClick, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled}
        onClick={(e) => {
          if (onPress) onPress(e);
          if (onClick) onClick(e);
        }}
        className={`cursor-pointer transition ${className}`}
        style={style}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Pressable.displayName = 'Pressable';

export const ScrollView = React.forwardRef<HTMLDivElement, any>(
  ({ className = '', style, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`overflow-y-auto ${className}`}
        style={style}
        {...props}
      >
        {children}
      </div>
    );
  }
);
ScrollView.displayName = 'ScrollView';

export const TextInput = React.forwardRef<HTMLInputElement | HTMLTextAreaElement, any>(
  (
    {
      className = '',
      style,
      value,
      onChangeText,
      onChange,
      onSubmitEditing,
      onKeyDown,
      placeholder,
      placeholderTextColor,
      secureTextEntry,
      multiline,
      numberOfLines = 3,
      keyboardType,
      ...props
    },
    ref
  ) => {
    const handleChange = (e: any) => {
      if (onChangeText) onChangeText(e.target.value);
      if (onChange) onChange(e);
    };

    const handleKeyDown = (e: any) => {
      if (e.key === 'Enter' && !multiline && onSubmitEditing) {
        e.preventDefault();
        onSubmitEditing();
      }
      if (onKeyDown) onKeyDown(e);
    };

    if (multiline) {
      return (
        <textarea
          ref={ref as any}
          rows={numberOfLines}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={className}
          style={style}
          {...props}
        />
      );
    }

    return (
      <input
        ref={ref as any}
        type={secureTextEntry ? 'password' : 'text'}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={className}
        style={style}
        {...props}
      />
    );
  }
);
TextInput.displayName = 'TextInput';

export const Image = React.forwardRef<HTMLImageElement, any>(
  ({ className = '', style, source, src, alt = '', ...props }, ref) => {
    const imageUri = typeof source === 'object' && source?.uri ? source.uri : src;
    return (
      <img
        ref={ref}
        src={imageUri}
        alt={alt}
        className={className}
        style={style}
        {...props}
      />
    );
  }
);
Image.displayName = 'Image';

export const StyleSheet = {
  create: <T extends Record<string, any>>(styles: T): T => styles,
};

export const Platform = {
  OS: 'web',
  select: <T extends Record<string, any>>(obj: T): any => obj.web || obj.default,
};
