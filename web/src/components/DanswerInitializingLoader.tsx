import { Bold } from "@tremor/react";
import Image from "next/image";

export function DanswerInitializingLoader() {
  return (
    <div className="mx-auto animate-pulse">
      <Bold>Initializing ElectionGPT</Bold>
    </div>
  );
}
