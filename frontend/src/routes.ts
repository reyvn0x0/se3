import { type RouteConfig, layout, index } from "@react-router/dev/routes";

export default [
  layout("./components/app-layout.tsx", [index("./pages/Home.tsx")]),
] satisfies RouteConfig;
