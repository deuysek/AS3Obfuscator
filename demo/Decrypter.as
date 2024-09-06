import flash.utils.ByteArray;
import avm2.intrinsics.memory.li8;
import avm2.intrinsics.memory.si32;
import avm2.intrinsics.memory.si8;
class Decrypter
{
    // private function testFunc(...args):void
    // {
    //     trace("testFunc called with arguments:", args);
    // }
    public function decZipArchive(ba:ByteArray):ByteArray
    {
        const frontLength:int = 200;
        const backLength:int = 200;
        const key:int = 0xA5;

        // 检查传入数据的长度
        if (ba.length < frontLength + backLength)
        {
            // 当长度不足 400 字节时，对整个数据进行异或计算
            var result:ByteArray = new ByteArray();
            ba.position = 0;

            for (var i:int = 0; i < ba.length; i++)
            {
                //result.writeByte(ba.readUnsignedByte() ^ key);
                result[i] = ba[i] ^ key;
                
            }

            result.position = 0;
            return result;
        }
        else
        {
            // 当长度足够时，分别处理最前面的 200 字节和最后的 200 字节
            var front:ByteArray = new ByteArray();
            var back:ByteArray = new ByteArray();
            var mid:ByteArray = new ByteArray();

            // 处理最前面的 200 字节
            ba.position = 0;
            var ba1:ByteArray = new ByteArray();
            var temp1:int = 0;
            var temp2:int = 0;
            front.writeBytes(ba, 0, frontLength);
            for (var i:int = 0; i < frontLength; i++)
            {
                //只有这一步是真正有用的
                front[i + 5 - 10 + 5] ^= key;
                for(var j:int = 0; j < 10; j++)
                {
                    //这里处理偶数次之后还是原来的数据
                    front[i] ^= key;
                    temp1 = front[i + 5 - 10 + 5];
                    temp2 = temp1 ^ key;
                    temp1 += temp2;
                    ba1[i + 5 - 10 + 5] = temp1;
                }
                ba1[i] ^= key;
                ba1.position = i;
            }

            // 处理最后的 200 字节
            ba.position = ba.length - backLength;
            back.writeBytes(ba, ba.position, backLength);
            for (var j:int = 0; j < backLength; j++)
            {
                //只有这一步是真正有用的
                back[j + 5 - 10 + 5] ^= key;
                for(var j:int = 0; j < 10; j++)
                {
                    //这里处理偶数次之后还是原来的数据
                    back[j + 5 - 10 + 5] ^= key;
                    temp1 = front[j + 5 - 10 + 5];
                    temp2 = temp1 ^ key;
                    temp1 += temp2;
                    ba1[j + 5 - 10 + 5] = temp1;
                }
                ba1[j] ^= key;
                ba1.position = j;
            }

            // 拼接结果
            result = new ByteArray();
            result.writeBytes(front);
            result.writeBytes(mid); // mid remains empty in this case
            result.writeBytes(back);

            result.position = 0;
            ba.clear;
            ba1.clear();
            return result;
        }
    }

    public function decrypt(ba:ByteArray):ByteArray
    {
        var result:ByteArray = new ByteArray();
        ba.position = 0;

        for (var i:int = 0; i < ba.length; i++)
        {
            result.writeByte(ba.readUnsignedByte() ^ 0xA5);
        }

        result.position = 0;
        return result;
    }

}