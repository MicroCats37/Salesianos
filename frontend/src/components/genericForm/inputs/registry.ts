// genericForm/inputs/registry.ts
// Central registry of all available inputs

import { FormattedNumberInput } from "./FormattedNumberInput";
import { InputCheckbox } from "./InputCheckbox";
import { InputDatePicker } from "./InputDatePicker";
import { InputFileCollection } from "./InputFileCollection";
import { InputFormattedNumber } from "./InputFormattedNumber";
import { InputHidden } from "./InputHidden";
import { InputImage } from "./InputImage";
import { InputNumber } from "./InputNumber";
import { InputPassword } from "./InputPassword";
import { InputRadio } from "./InputRadio";
import { InputSearchableSelect } from "./InputSearchableSelect";
import { InputSelect } from "./InputSelect";
import { InputText } from "./InputText";
import { InputTextarea } from "./InputTextarea";
import type { InputComponent } from "./types";

export const inputRegistry: Record<string, InputComponent> = {
  text: InputText,
  number: InputNumber,
  textarea: InputTextarea,
  password: InputPassword,
  select: InputSelect,
  "searchable-select": InputSearchableSelect,
  radio: InputRadio,
  checkbox: InputCheckbox,
  hidden: InputHidden,
  date: InputDatePicker,
  image: InputImage,
  "formatted-number": InputFormattedNumber,
  "file-collection": InputFileCollection,
};

export const getInputComponent = (type: string): InputComponent => {
  const component = inputRegistry[type];
  if (!component) {
    console.warn(
      `Input type "${type}" not found in registry. Using InputText as fallback.`,
    );
    return InputText;
  }
  return component;
};

export const registerInput = (
  type: string,
  component: InputComponent,
): void => {
  if (inputRegistry[type]) {
    console.warn(
      `Input type "${type}" already exists and will be overwritten.`,
    );
  }
  inputRegistry[type] = component;
};
