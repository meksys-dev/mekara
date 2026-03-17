import { type ReactNode } from "react";
import OriginalDocBreadcrumbs from "@theme-original/DocBreadcrumbs";
import DocVersionBadge from "@theme-original/DocVersionBadge";

export default function DocBreadcrumbs(): ReactNode {
  return (
    <div
      className="breadcrumbs-version-row"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <OriginalDocBreadcrumbs />
      <DocVersionBadge />
    </div>
  );
}
