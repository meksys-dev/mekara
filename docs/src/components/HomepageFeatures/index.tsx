import type { ComponentProps, ComponentType, ReactNode } from "react";
import clsx from "clsx";
import Heading from "@theme/Heading";
import styles from "./styles.module.css";
import MountainSvg from "@site/static/img/undraw_docusaurus_mountain.svg";
import TreeSvg from "@site/static/img/undraw_docusaurus_tree.svg";
import ReactSvg from "@site/static/img/undraw_docusaurus_react.svg";

type FeatureItem = {
  title: string;
  Svg: ComponentType<ComponentProps<"svg">>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: "Built for mekara",
    Svg: MountainSvg,
    description: (
      <>
        Every page documents the real Python CLI that lives in this repo, from
        module layout to release automation expectations.
      </>
    ),
  },
  {
    title: "Actionable workflows",
    Svg: TreeSvg,
    description: (
      <>
        Build, lint, and testing recipes mirror the commands we expect in CI so
        you can reproduce failures locally in seconds.
      </>
    ),
  },
  {
    title: "Always current",
    Svg: ReactSvg,
    description: (
      <>
        Documentation updates live in the same PRs as code changes. No more
        stale AGENTS files or mismatched CLI instructions.
      </>
    ),
  },
];

function Feature({ title, Svg, description }: FeatureItem) {
  return (
    <div className={clsx("col col--4")}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
