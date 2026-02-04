import useDocusaurusContext from "@docusaurus/useDocusaurusContext";

export default function Version() {
  const { siteConfig } = useDocusaurusContext();
  const version = (siteConfig.customFields?.version as string) || "";
  return <span>{version}</span>;
}
