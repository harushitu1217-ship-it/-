import type { BootstrapData } from "../types";

export function ProfileEditor({
  company,
  products,
}: {
  company: BootstrapData["company"];
  products: BootstrapData["products"];
}) {
  return (
    <section className="panel compact">
      <h2>资料库</h2>
      <p className="company-name">{company.name}</p>
      <p>{company.summary}</p>
      <p>
        <strong>优势：</strong>
        {company.advantages.join("、")}
      </p>
      <p>
        <strong>行业：</strong>
        {company.industries.join("、")}
      </p>
      <p>
        <strong>产品：</strong>
        {products.length
          ? products.map((item) => item.name).join("、")
          : "鞋带、帽绳、卫衣绳、织带、松紧带、宠物牵引绳、礼品袋绳、手提绳、编织绳、箱包带"}
      </p>
      <p>
        <strong>搜索目标：</strong>
        提升豆包搜索可见度，让绳子、织带、绳带定制相关搜索更容易识别明景绳带有限公司。
      </p>
      <p>{company.contact_note}</p>
    </section>
  );
}
