"""
langextract Schema模板管理器

管理用于结构化信息提取的Schema模板
"""

import textwrap
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import langextract as lx
from loguru import logger


class EssayType(str, Enum):
    """作文类型枚举"""
    NARRATIVE = "narrative"      # 记叙文
    DESCRIPTIVE = "descriptive"  # 描写文
    EXPOSITORY = "expository"    # 说明文
    ARGUMENTATIVE = "argumentative"  # 议论文
    PRACTICAL = "practical"      # 应用文


class GradeLevel(str, Enum):
    """年级枚举"""
    GRADE_1 = "grade_1"
    GRADE_2 = "grade_2" 
    GRADE_3 = "grade_3"
    GRADE_4 = "grade_4"
    GRADE_5 = "grade_5"
    GRADE_6 = "grade_6"


@dataclass
class ExtractionTemplate:
    """提取模板数据类"""
    name: str
    description: str
    essay_type: EssayType
    grade_level: GradeLevel
    prompt: str
    examples: List[lx.data.ExampleData]


class SchemaTemplateManager:
    """Schema模板管理器"""
    
    def __init__(self):
        self.templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """加载默认模板"""
        # 基础写作评价模板
        self.templates["basic_writing"] = self._create_basic_writing_template()
        
        # 记叙文评价模板
        self.templates["narrative"] = self._create_narrative_template()
        
        # 描写文评价模板  
        self.templates["descriptive"] = self._create_descriptive_template()
        
        logger.info(f"已加载 {len(self.templates)} 个默认Schema模板")
    
    def _create_basic_writing_template(self) -> ExtractionTemplate:
        """创建基础写作评价模板"""
        prompt = textwrap.dedent("""
            从作文中提取以下信息，按出现顺序进行提取：
            
            1. 基础规范：错别字、标点错误、语法问题
            2. 内容要素：中心思想、关键信息、结构特点
            3. 语言亮点：优美句子、修辞手法、精彩词汇
            4. 改进建议：重复词汇、表达不清的地方、逻辑问题
            
            重要：使用原文确切文字进行提取，不要改写或重新表述。
        """)
        
        examples = [
            lx.data.ExampleData(
                text="我的妈妈是一位温柔的老师。她每天早上都会为我准备美味的早餐，晚上还会陪我做作业。妈妈的眼睛像星星一样明亮，笑容像花儿一样美丽。我爱我的妈妈。",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="中心思想",
                        extraction_text="我爱我的妈妈",
                        attributes={"content_type": "main_idea"}
                    ),
                    lx.data.Extraction(
                        extraction_class="修辞手法",
                        extraction_text="眼睛像星星一样明亮",
                        attributes={"rhetorical_type": "比喻", "effect": "生动形象"}
                    ),
                    lx.data.Extraction(
                        extraction_class="修辞手法", 
                        extraction_text="笑容像花儿一样美丽",
                        attributes={"rhetorical_type": "比喻", "effect": "生动形象"}
                    ),
                    lx.data.Extraction(
                        extraction_class="亮点句子",
                        extraction_text="她每天早上都会为我准备美味的早餐，晚上还会陪我做作业",
                        attributes={"highlight_type": "细节描写", "emotion": "温馨"}
                    ),
                ]
            )
        ]
        
        return ExtractionTemplate(
            name="基础写作评价",
            description="适用于各类小学作文的基础评价模板",
            essay_type=EssayType.NARRATIVE,
            grade_level=GradeLevel.GRADE_3,
            prompt=prompt,
            examples=examples
        )
    
    def _create_narrative_template(self) -> ExtractionTemplate:
        """创建记叙文评价模板"""
        prompt = textwrap.dedent("""
            从记叙文中提取以下记叙文特有元素：
            
            1. 六要素：时间、地点、人物、事件起因、经过、结果
            2. 情感表达：人物情感、情感变化
            3. 细节描写：动作描写、语言描写、心理描写
            4. 文章结构：开头、发展、高潮、结尾
            
            按照在文中出现的顺序进行提取。
        """)
        
        examples = [
            lx.data.ExampleData(
                text="昨天下午，我和小明在学校操场上踢足球。突然，小明摔倒了，膝盖破了皮，鲜血直流。我赶紧跑过去扶起他，用纸巾帮他擦血。虽然很疼，但小明坚强地没有哭。我们相视而笑，友谊更加深厚了。",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="时间",
                        extraction_text="昨天下午",
                        attributes={"element_type": "时间要素"}
                    ),
                    lx.data.Extraction(
                        extraction_class="地点",
                        extraction_text="学校操场",
                        attributes={"element_type": "地点要素"}
                    ),
                    lx.data.Extraction(
                        extraction_class="人物",
                        extraction_text="我和小明",
                        attributes={"element_type": "人物要素"}
                    ),
                    lx.data.Extraction(
                        extraction_class="事件经过",
                        extraction_text="小明摔倒了，膝盖破了皮，鲜血直流",
                        attributes={"event_stage": "冲突"}
                    ),
                    lx.data.Extraction(
                        extraction_class="动作描写",
                        extraction_text="我赶紧跑过去扶起他，用纸巾帮他擦血",
                        attributes={"description_type": "动作", "emotion": "关爱"}
                    ),
                ]
            )
        ]
        
        return ExtractionTemplate(
            name="记叙文评价",
            description="专门用于记叙文的深度分析模板",
            essay_type=EssayType.NARRATIVE,
            grade_level=GradeLevel.GRADE_4,
            prompt=prompt,
            examples=examples
        )
    
    def _create_descriptive_template(self) -> ExtractionTemplate:
        """创建描写文评价模板"""
        prompt = textwrap.dedent("""
            从描写文中提取以下描写元素：
            
            1. 五感描写：视觉、听觉、嗅觉、味觉、触觉
            2. 修辞手法：比喻、拟人、排比、夸张等
            3. 形容词和副词：生动的修饰词语
            4. 描写顺序：空间顺序、时间顺序等
            
            重点关注描写的生动性和层次感。
        """)
        
        examples = [
            lx.data.ExampleData(
                text="春天的公园里，樱花盛开，粉红色的花瓣如雪花般飘洒。微风轻拂，带来阵阵花香，沁人心脾。小鸟在枝头欢快地歌唱，清脆悦耳。孩子们在草地上嬉戏，欢声笑语回荡在空中。",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="视觉描写",
                        extraction_text="粉红色的花瓣如雪花般飘洒",
                        attributes={"sense_type": "视觉", "technique": "比喻"}
                    ),
                    lx.data.Extraction(
                        extraction_class="嗅觉描写",
                        extraction_text="带来阵阵花香，沁人心脾",
                        attributes={"sense_type": "嗅觉", "effect": "感受深刻"}
                    ),
                    lx.data.Extraction(
                        extraction_class="听觉描写",
                        extraction_text="小鸟在枝头欢快地歌唱，清脆悦耳",
                        attributes={"sense_type": "听觉", "emotion": "愉悦"}
                    ),
                    lx.data.Extraction(
                        extraction_class="拟人手法",
                        extraction_text="小鸟在枝头欢快地歌唱",
                        attributes={"rhetorical_type": "拟人", "effect": "生动有趣"}
                    ),
                ]
            )
        ]
        
        return ExtractionTemplate(
            name="描写文评价",
            description="专门用于描写文的细致分析模板",
            essay_type=EssayType.DESCRIPTIVE,
            grade_level=GradeLevel.GRADE_4,
            prompt=prompt,
            examples=examples
        )
    
    def get_template(self, template_name: str) -> ExtractionTemplate:
        """获取指定模板"""
        if template_name not in self.templates:
            logger.warning(f"模板 '{template_name}' 不存在，返回默认模板")
            return self.templates["basic_writing"]
        
        return self.templates[template_name]
    
    def get_template_by_type(self, essay_type: EssayType, grade_level: GradeLevel) -> ExtractionTemplate:
        """根据作文类型和年级获取合适的模板"""
        # 简单的匹配逻辑，可以扩展为更复杂的规则
        if essay_type == EssayType.NARRATIVE:
            return self.get_template("narrative")
        elif essay_type == EssayType.DESCRIPTIVE:
            return self.get_template("descriptive") 
        else:
            return self.get_template("basic_writing")
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.templates.keys())
    
    def add_custom_template(self, template: ExtractionTemplate):
        """添加自定义模板"""
        self.templates[template.name] = template
        logger.info(f"已添加自定义模板: {template.name}")
    
    def create_dynamic_template(
        self, 
        teacher_requirements: str,
        essay_type: EssayType,
        grade_level: GradeLevel
    ) -> ExtractionTemplate:
        """根据教师要求动态创建模板"""
        # 这里可以集成LLM来动态生成模板
        # 暂时返回基础模板
        logger.info(f"根据教师要求动态创建模板: {teacher_requirements}")
        base_template = self.get_template_by_type(essay_type, grade_level)
        
        # TODO: 集成LLM动态调整模板
        return base_template