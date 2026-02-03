/**
 * Image Recognition Tool
 *
 * Allows the agent to read and analyze local image files using the configured LLM provider.
 */

import { tool } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';
import { readFile, access, stat } from 'fs/promises';
import { extname } from 'path';

/**
 * Media type mapping for supported image formats
 */
const MEDIA_TYPE_MAP: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
};

/**
 * Maximum file size (5MB)
 */
const MAX_FILE_SIZE = 5 * 1024 * 1024;

/**
 * Supported image extensions
 */
const SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp'];

/**
 * Create the RecognizeImage tool
 *
 * @param apiKey - API key for the LLM provider
 * @param baseUrl - Base URL for the API (optional)
 * @param model - Model to use for recognition (optional)
 */
export function createRecognizeImageTool(
  apiKey: string,
  baseUrl?: string,
  model?: string
) {
  return tool(
    'RecognizeImage',
    `识别和分析图片内容。当需要查看、理解或分析图片文件时使用此工具。

支持的格式: PNG, JPG, JPEG, GIF, WEBP
最大文件大小: 5MB

使用场景:
- 识别验证码
- 分析截图内容
- 理解图表和数据可视化
- 提取图片中的文字
- 描述图片内容`,
    {
      imagePath: z
        .string()
        .describe('图片文件的绝对路径,例如: /path/to/image.png'),
      question: z
        .string()
        .optional()
        .describe(
          '关于图片的问题或需要分析的内容(可选)。例如: "请识别验证码", "请描述图片内容", "请提取图片中的文字"。默认为"请描述这张图片的内容"'
        ),
    },
    async (args) => {
      try {
        // 1. Check if file exists
        try {
          await access(args.imagePath);
        } catch {
          return {
            content: [
              {
                type: 'text' as const,
                text: `文件不存在: ${args.imagePath}`,
              },
            ],
            isError: true,
          };
        }

        // 2. Check file size
        const stats = await stat(args.imagePath);
        if (stats.size > MAX_FILE_SIZE) {
          return {
            content: [
              {
                type: 'text' as const,
                text: `图片文件过大 (${(stats.size / 1024 / 1024).toFixed(2)}MB),超过 5MB 限制。请使用较小的图片。`,
              },
            ],
            isError: true,
          };
        }

        // 3. Check file format
        const ext = extname(args.imagePath).toLowerCase();
        if (!SUPPORTED_EXTENSIONS.includes(ext)) {
          return {
            content: [
              {
                type: 'text' as const,
                text: `不支持的图片格式: ${ext}。支持的格式: ${SUPPORTED_EXTENSIONS.join(', ')}`,
              },
            ],
            isError: true,
          };
        }

        // 4. Read and encode image
        const imageData = await readFile(args.imagePath);
        const base64Image = imageData.toString('base64');
        const mediaType = MEDIA_TYPE_MAP[ext] || 'image/png';

        // 5. Prepare API request
        const apiBaseUrl = baseUrl || 'https://api.anthropic.com';
        const apiModel = model || 'claude-sonnet-4-20250514';
        const question = args.question || '请描述这张图片的内容';

        console.log('[RecognizeImage] Analyzing image:', {
          path: args.imagePath,
          size: `${(stats.size / 1024).toFixed(2)}KB`,
          format: ext,
          question: question.slice(0, 50),
        });

        // 6. Call LLM API
        const response = await fetch(`${apiBaseUrl}/v1/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
          },
          body: JSON.stringify({
            model: apiModel,
            max_tokens: 2048,
            messages: [
              {
                role: 'user',
                content: [
                  {
                    type: 'image',
                    source: {
                      type: 'base64',
                      media_type: mediaType,
                      data: base64Image,
                    },
                  },
                  {
                    type: 'text',
                    text: question,
                  },
                ],
              },
            ],
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('[RecognizeImage] API error:', {
            status: response.status,
            error: errorText,
          });
          return {
            content: [
              {
                type: 'text' as const,
                text: `API 调用失败 (HTTP ${response.status}): ${errorText}`,
              },
            ],
            isError: true,
          };
        }

        // 7. Parse response
        const result = (await response.json()) as {
          content?: Array<{ type: string; text?: string }>;
          error?: { message: string };
        };

        if (result.error) {
          return {
            content: [
              {
                type: 'text' as const,
                text: `识别失败: ${result.error.message}`,
              },
            ],
            isError: true,
          };
        }

        const text =
          result.content?.find((c) => c.type === 'text')?.text ||
          '无法识别图片内容';

        console.log('[RecognizeImage] Recognition successful:', {
          resultLength: text.length,
        });

        return {
          content: [
            {
              type: 'text' as const,
              text,
            },
          ],
        };
      } catch (error) {
        console.error('[RecognizeImage] Error:', error);
        return {
          content: [
            {
              type: 'text' as const,
              text: `图片识别失败: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }
  );
}
