import { UnderDevelopment } from "@/components/course/UnderDevelopment";
import { LegacyRedirect } from "@/components/course/LegacyRedirect";

export default function NotFound() {
  return (
    <>
      <LegacyRedirect />
      <UnderDevelopment
        title="Still in Training"
        description="This page hasn't shipped yet - we're fine-tuning it behind the scenes. Check back soon, or jump back into the curriculum below."
      />
    </>
  );
}
