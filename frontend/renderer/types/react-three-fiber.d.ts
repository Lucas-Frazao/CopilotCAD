declare module "@react-three/fiber" {
  import type { ReactNode } from "react";

  export function Canvas(props: { children?: ReactNode }): JSX.Element;
}